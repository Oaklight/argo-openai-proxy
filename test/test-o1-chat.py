from openai import OpenAI

client = OpenAI(api_key="random+whatever", base_url="http://localhost:5000/v1")

user_prompt = """
Instructions:
- Given the React component below, change it so that nonfiction books have red
  text. 
- Return only the code in your reply
- Do not include any additional formatting, such as markdown code blocks
- For formatting, use four space tabs, and do not allow any lines of code to 
  exceed 80 columns

const books = [
  { title: 'Dune', category: 'fiction', id: 1 },
  { title: 'Frankenstein', category: 'fiction', id: 2 },
  { title: 'Moneyball', category: 'nonfiction', id: 3 },
];

export default function BookList() {
  const listItems = books.map(book =>
    <li>
      {book.title}
    </li>
  );

  return (
    <ul>{listItems}</ul>
  );
}
"""

response = client.chat.completions.create(
    model="argo:gpt-o1-preview",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
            ],
        },
    ],
)

print(response.choices[0].message.content)

# Define the system prompt
system_prompt = (
    "You are a helpful assistant that provides information and answers questions."
)

# Combine the system prompt with the user's input
prompt = f"{system_prompt}\n\nUser: {user_prompt}"

# Make the API call
response = client.completions.create(
    model="argo:gpt-o1-preview",
    prompt=prompt,
    max_tokens=200,
    temperature=0.7,
)

# Print the response
print(response.choices[0].text)
