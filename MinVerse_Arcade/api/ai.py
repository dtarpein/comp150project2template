def fliptext_prompt():
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "Give me a funny sentence."}]
    )
    return response.choices[0].message.content.strip()
