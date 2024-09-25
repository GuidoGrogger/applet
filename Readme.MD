# Applet Creator

## Description
Applet Creator is a web application designed to help users create smart notes and lightweight apps through voice commands. It showcases how you can generate apps using voice and AI, providing an educational experience for users interested in this technology. Users can record their voice to generate applets for daily tasks, reminders, and small projects. The app allows easy sharing of these applets with friends and colleagues, making it a convenient tool for enhancing productivity.

### Features
- **Voice Recording**: Users can record their voice to create applets.
- **Applet Management**: Users can create new applets, change existing ones, and share them easily.
- **User-Friendly Interface**: The application provides a simple and intuitive interface for users to interact with.

## Disclaimer
This application is a prototype and is not fully production-ready. Use it at your own risk. The developers are not responsible for any issues that may arise from its use. Please provide feedback to help improve the application.

# Setting up the Virtual Python Environment

1. Ensure you have Python installed. You can download it from [python.org](https://www.python.org/).

2. Open your terminal or command prompt.

3. Navigate to the project directory:
    ```sh
    cd /path/to/your/project
    ```

4. Create a virtual environment:
    ```sh
    python -m venv venv
    ```

5. Activate the virtual environment:
    - On Windows:
        ```sh
        .\venv\Scripts\activate
        ```
    - On macOS and Linux:
        ```sh
        source venv/bin/activate
        ```

6. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```
7. Get Groq API key and set as an environment variable:
    ```sh
    export GROQ_API_KEY=<your_api_key>
    ``` 
    You can get the API key from [Groq](https://console.groq.com/).



## Starting the server

1. Activate the virtual environment (if not already activated):
    ```sh
    # Check if the virtual environment is active
    if [ -z "$VIRTUAL_ENV" ]; then
        source venv/bin/activate  # For macOS and Linux
        # .\venv\Scripts\activate  # Uncomment for Windows
    fi
    ```

2. To start the server locally, run:
    ```sh
    ./venv/bin/python app.py
    ```

3. Open your web browser and navigate to:
    ```sh
    http://127.0.0.1:5000
    ```

4. To deactivate the virtual environment, simply run:
    ```sh
    deactivate
    ```

## Running tests

1. Activate the virtual environment (if not already activated):
    ```sh
    # Check if the virtual environment is active
    if [ -z "$VIRTUAL_ENV" ]; then
        source venv/bin/activate  # For macOS and Linux
        # .\venv\Scripts\activate  # Uncomment for Windows
    ```

2. Run the tests:
    ```sh
    ./venv/bin/python test_app.py
    ```
2.1 For running just a single test:
    ```sh
    ./venv/bin/python -m unittest test_app.AppletTestCase.test_show_applet_html
    ```

## TODOs
- **Images**: Ensure images load correctly; consider using ready-made icons.
- **Font Awesome**: Confirm the addition of the Font Awesome CDN for icon usage.
- **Design**: Define the overall design approach.
- **Prompt Appearance**: Determine how the prompt should look and whether to ask the user beforehand.
- **User Feedback**: Provide feedback on the prompt and avoid timing issues, as they can be unpredictable. Inform the user about this.