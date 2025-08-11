import openai
import random
import time
import asyncio
from openai import AsyncOpenAI

class Request():
    def __init__(self, config):
        self.config = config
        self.async_client = AsyncOpenAI(api_key=self.config['openai_api_key'])

 
    async def single_request(self, user, system=None, seed_value=None):

        if system:
            message = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        else:
            message = [{"role": "user", "content": user}]
        
        # Reimplemented the robust retry loop with exponential backoff
        for delay_secs in (2**x for x in range(0, 3)):
            try:
                response = await self.async_client.chat.completions.create(
                    model=self.config['model'],
                    messages=message,
                    temperature=0.2,
                    max_tokens=1500,
                    seed=seed_value
                )
                return response.choices[0].message.content.strip()
            except openai.OpenAIError as e:
                randomness_collision_avoidance = random.randint(0, 1000) / 1000.0
                sleep_dur = delay_secs + randomness_collision_avoidance
                print(f"Error: {e}. Retrying in {round(sleep_dur, 2)} seconds.")
                await asyncio.sleep(sleep_dur)
        
        # Return None if all retries fail
        return None


    async def openai_request(self, prompts, system=None, batch_size=128, delay=5):

        results = []

        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i+batch_size]
            tasks = [
                self.single_request(d["prompts"], system=system, seed_value=self.config['seed'])
                for j, d in enumerate(batch)
            ]

            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            print(f"✅ Sending batch {i // batch_size + 1} — sleeping for {delay}s...\n")
            await asyncio.sleep(delay)

        return results
    
    # def request(self, user, system=None, message=None):
    #     response = self.openai_request(user, system, message)

    #     return response
    
    # def openai_request(self, user, system=None, message=None):
    #     '''
    #     fix openai communicating error
    #     https://community.openai.com/t/openai-error-serviceunavailableerror-the-server-is-overloaded-or-not-ready-yet/32670/19
    #     '''
    #     if system:
    #         message=[{"role":"system", "content":system}, {"role": "user", "content": user}]
    #     else:
    #         content = system + user
    #         message=[{"role": "user", "content": content}]
    #     model = self.conifg['model']
    #     for delay_secs in (2**x for x in range(0, 10)):
    #         try:
    #             response = openai.chat.completions.create(
    #                 model=model,
    #                 messages = message,
    #                 temperature=0.2,
    #                 max_tokens = 1500)
    #             break
    #         except openai.OpenAIError as e:
    #             randomness_collision_avoidance = random.randint(0, 1000) / 1000.0
    #             sleep_dur = delay_secs + randomness_collision_avoidance
    #             print(f"Error: {e}. Retrying in {round(sleep_dur, 2)} seconds.")
    #             time.sleep(sleep_dur)
    #             continue
        
    #     return response.choices[0].message.content
