## Response Relevancy

The `ResponseRelevancy` metric measures how relevant a response is to the user input. Higher scores indicate better alignment with the user input, while lower scores are given if the response is incomplete or includes redundant information.  

This metric is calculated using the `user_input` and the `response` as follows:  

1. Generate a set of artificial questions (default is 3) based on the response. These questions are designed to reflect the content of the response.  
2. Compute the cosine similarity between the embedding of the user input ($E_o$) and the embedding of each generated question ($E_{g_i}$).  
3. Take the average of these cosine similarity scores to get the **Answer Relevancy**:  

$$
\text{Answer Relevancy} = \frac{1}{N} \sum_{i=1}^{N} \text{cosine similarity}(E_{g_i}, E_o)
$$  

$$
\text{Answer Relevancy} = \frac{1}{N} \sum_{i=1}^{N} \frac{E_{g_i} \cdot E_o}{\|E_{g_i}\| \|E_o\|}
$$  

Where:  
- $E_{g_i}$: Embedding of the $i^{th}$ generated question.  
- $E_o$: Embedding of the user input.  
- $N$: Number of generated questions (default is 3).  

**Note**: While the score usually falls between 0 and 1, it is not guaranteed due to cosine similarity's mathematical range of -1 to 1.

An answer is considered relevant if it directly and appropriately addresses the original question. This metric focuses on how well the answer matches the intent of the question, without evaluating factual accuracy. It penalizes answers that are incomplete or include unnecessary details.

### Example

```python
from ragas import SingleTurnSample 
from ragas.metrics import ResponseRelevancy

sample = SingleTurnSample(
        user_input="When was the first super bowl?",
        response="The first superbowl was held on Jan 15, 1967",
        retrieved_contexts=[
            "The First AFL–NFL World Championship Game was an American football game played on January 15, 1967, at the Los Angeles Memorial Coliseum in Los Angeles."
        ]
    )

scorer = ResponseRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings)
await scorer.single_turn_ascore(sample)
```
Output
```
0.9165088378587264
```

### How It’s Calculated

!!! example
    Question: Where is France and what is it's capital?

    Low relevance answer: France is in western Europe.

    High relevance answer: France is in western Europe and Paris is its capital.

To calculate the relevance of the answer to the given question, we follow two steps:

- **Step 1:** Reverse-engineer 'n' variants of the question from the generated answer using a Large Language Model (LLM). 
  For instance, for the first answer, the LLM might generate the following possible questions:
    - *Question 1:* "In which part of Europe is France located?"
    - *Question 2:* "What is the geographical location of France within Europe?"
    - *Question 3:* "Can you identify the region of Europe where France is situated?"

- **Step 2:** Calculate the mean cosine similarity between the generated questions and the actual question.

The underlying concept is that if the answer correctly addresses the question, it is highly probable that the original question can be reconstructed solely from the answer.
