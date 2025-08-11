import random
from opt.utils import detect_error, extract_edit_prompt, extract_bundle_score

class Improve():
    def __init__(self,
                inferring_reasons, 
                refining_prompts, 
                augmenting_prompts, 
                train_data,
                config,
                request_model):
        self.inferring_reasons = inferring_reasons
        self.refining_prompts = refining_prompts
        self.augmenting_prompts = augmenting_prompts
        self.train_data = train_data
        self.config = config
        self.request = request_model
        self.used_data = []
    
    async def evaluate_collect_error(self, system_prompt, data):
        errors_list = []
        prompt_list = [{"prompts": val['input'] + "\n" + self.config['json_addition']} for val in data]
        
        # print("System Prompt:\n", system_prompt)
        # print()
        # print("User Prompt:\n", prompt_list[0]["prompts"])


        responses = await self.request.openai_request(prompt_list, system_prompt)
        validation_targets = [val['target_score'] for val in data]

        for i in range(len(responses)):
            given_score = extract_bundle_score(responses[i])
            validation_score = validation_targets[i]

            if not detect_error(given_score, validation_score):
                error = {}
                error['input'] = data[i]['input']
                error['output'] = responses[i]
                error['given_score'] = given_score
                error['true_score'] = validation_score
                error['annotation'] = data[i]['annotations']
                errors_list.append(error)
    
        return errors_list

    async def generate_similar_prompt(self, prompt_list):
        # Step 1: Augment each prompt once to create a temporary list
        tmp = self.augmenting_prompts
        augmented_prompts_once = [
            tmp.replace("$refined_prompt$", prompt) 
            for prompt in prompt_list
        ]

        # Step 2: Create a flattened list where each augmented prompt is repeated
        # 'addition_sample' times, which is what your proposed line does.
        flattened_prompts = [
            p for p in augmented_prompts_once 
            for _ in range(self.config['addition_sample'])
        ]
        
        # Step 3: Format the flattened list into the dictionary format
        formatted_prompts = [{"prompts": p} for p in flattened_prompts]

        # print("Asking us to make an augmented prompt. Actually check if we've used the augmenting prompt and replaced the real prompt\n")

        # print(formatted_prompts[0]["prompts"])

        # Step 4: Send all formatted prompts in one asynchronous batch
        # We assume the augmentation prompt has no system message, hence system=None
        responses = await self.request.openai_request(prompts=formatted_prompts)
    
        return responses

    async def run(self, prompt, table=None):

        train_data_values = list(self.train_data.values())
    
        # Sample from the list of values to get a list of dictionaries
        batch_data = random.sample(train_data_values, self.config['batch_size'])
      
        # batch_data = dict(random.sample(list(self.train_data.items()), self.config['batch_size']))
        
        self.used_data += batch_data

        print("Evaluating Bundles and collecting errors\n")

        errors_list = await self.evaluate_collect_error(prompt, batch_data) 

        try:
            errors_group = random.sample(errors_list, self.config['error_batch_size'])
        except:
            errors_group = errors_list

        inferring_reasons = self.inferring_reasons.replace("$prompt$", prompt).replace("$num_feedbacks$", str(self.config['num_feedbacks'])) 
        refining_prompts = self.refining_prompts.replace("$prompt$", prompt)

        
        tmp_infer_prompt = inferring_reasons
        # error_prompts = [tmp_infer_prompt.replace("$error_case$", error['input']).replace("$given_score$", str(error['given_score'])).replace("$true_score$", str(error['true_score'])) for error in errors_group]
        error_prompts = [tmp_infer_prompt.replace("$error_case$", error['input']).replace("$given_score$", str(error['given_score'])).replace("$true_score$", str(error['true_score'])).replace("$annotation$", error['annotation']) for error in errors_group]


        print()
        print("Trying to infer reasons for errors\n")

        error_prompts = [{"prompts": prompt} for prompt in error_prompts]

        # print("Sending in trying to find errors in example, there are no system prompts, please check our shit. I've added the scores and later expert annotations\n\n", error_prompts[0]["prompts"])

        gradients = await self.request.openai_request(error_prompts, system='')


        tmp_refine_prompt = refining_prompts
        tmp_refine_prompts = [tmp_refine_prompt.replace("$error_case$", error['input']) for error in errors_group]
        contents = [tmp_refine_prompts[i].replace("$reasons$", gradients[i]) for i in range(len(errors_group))]

        contents = [{"prompts": prompt} for prompt in contents]

        # print("Trying to refine prompts after injecting reasons\n")

        # print("No system prompts, but we've got reasons for why it might suck\n", contents[0]["prompts"])

        # Corrected: Passed a formatted list to the openai_request method
        edit_prompts_response = await self.request.openai_request(contents, system='')

        # Flatten the list of lists that extract_edit_prompt returns
        edit_prompt_list_flat = [
            item for sublist in [extract_edit_prompt(response) for response in edit_prompts_response] 
            for item in sublist
        ]

        print("We've refined prompts, now we're augmenting the refined prompts\n")

        candidate_prompts = await self.generate_similar_prompt(edit_prompt_list_flat)

        # Randomly sampled #num successor candidates per parent prompt
        try:
            sample_candidate_prompts = random.sample(candidate_prompts, self.config['num_candidates'])
        except:
            sample_candidate_prompts = candidate_prompts
        return sample_candidate_prompts
    
    def get_used_data(self):
        return self.used_data