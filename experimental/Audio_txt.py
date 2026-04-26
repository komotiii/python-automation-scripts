import speech_recognition as sr
from gtts import gTTS
import simpleaudio as sa
import nltk
from transformers import pipeline, Conversation

# Function to listen to the microphone
def listen_to_mic():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I did not understand that.")
        return None
    except sr.RequestError:
        print("Sorry, my speech service is down.")
        return None

# Function to process the text
def process_text(text):
    nltk.download('punkt')
    tokens = nltk.word_tokenize(text)
    print(f"Tokens: {tokens}")
    return tokens

# Function to get a response from a Hugging Face conversational model
def get_ai_response(prompt, conversation_pipeline):
    conversation = Conversation(prompt)
    response = conversation_pipeline(conversation)
    return response.generated_responses[0]

# Function to convert text to speech and play it
def speak(text):
    tts = gTTS(text=text, lang='en')
    tts.save("output.mp3")
    wave_obj = sa.WaveObject.from_wave_file("output.mp3")
    play_obj = wave_obj.play()
    play_obj.wait_done()

# Main function
def main():
    # Initialize the Hugging Face conversational model
    conversation_pipeline = pipeline("conversational", model="microsoft/DialoGPT-medium")

    print("Starting English learning helper...")
    while True:
        user_input = listen_to_mic()
        if user_input:
            ai_prompt = f"You are an English tutor. Correct any mistakes and provide suggestions to improve this sentence: '{user_input}'"
            ai_response = get_ai_response(ai_prompt, conversation_pipeline)
            print(f"AI Response: {ai_response}")
            speak(ai_response)

if __name__ == "__main__":
    main()
