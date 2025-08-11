import numpy as np
from opt.utils import detect_error, extract_bundle_score

# def ndcg(target_index):
#     res = 1 / np.log2(target_index + 1)
    
#     return res


def rmse(given_score, true_score):
    res = np.sqrt((given_score - true_score)**2)
    
    return res


class Reward():
    def __init__(self, config, request_model) -> None:
        self.config = config
        self.reward_func = config['reward_func']
        self.request = request_model

    async def calculate_reward(self, system_prompt, sample_data): # need to change this to prompt_list and send multiple at once
        epsilon = 0.1
        reward = 0


        prompt_list = [{"prompts": data['input'] + "\n" + self.config['json_addition']} for data in sample_data]

        print("System prompt:\n",system_prompt)

        print()

        print("Supposed to be sample data", prompt_list[0]["prompts"])


        print("Sending in prompts for da reward\n")

        responses = await self.request.openai_request(prompt_list, system_prompt)
        target_scores = [data['target_score'] for data in sample_data]


        for i in range(len(responses)):
            given_score = extract_bundle_score(responses[i])
            target_score = target_scores[i]

            if detect_error(given_score, target_score, mode='select'):
                reward += 1/(rmse(given_score, target_score) + epsilon)

        return reward

  
    # def calculate_reward(self, prompt, sample_data):
    #     reward = 0
    #     for data in sample_data:
    #         response = self.request.request(data['input'], prompt)
    #         if detect_error(response, data['target'], mode='select'):
    #             result_list = extract_item_list(response, data['target'])
    #             target_index = int(result_list[-1])
    #             reward = reward + rmse(target_index)

    #     return reward