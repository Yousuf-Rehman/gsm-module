# GSM Module SMS Processor

This Python script interfaces with GSM modules via serial communication to process incoming SMS messages. It also integrates with Telegram for notification purposes.

## Features

- **Message Processing**: Automatically reads incoming SMS messages from GSM modules.
- **Database Integration**: Stores message details in an SQLite database for later retrieval.
- **Telegram Integration**: Sends message notifications to a Telegram channel or user.
- **Multithreading**: Utilizes multithreading to handle multiple GSM modules simultaneously.
- **Signal Handling**: Gracefully stops all threads on SIGINT (Ctrl+C) signal.

## Usage

1. **Install Dependencies**:

   Make sure you have Python installed on your system. Install required Python packages using pip:

   ```bash
   pip install pyserial
   pip install python-telegram-bot
