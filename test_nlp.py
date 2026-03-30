from src.nlp_processor import NLPProcessor

processor = NLPProcessor()

text = "I did not authorize this payment and I don't recognize the merchant"

result = processor.process(text)

print(result)