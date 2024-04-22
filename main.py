import serial
import sys
import signal
import sqlite3
import time
import serial.tools.list_ports
import threading
import telegram_integaration

Number_List = []
Number_List_lock = threading.Lock()

NOT_FOUND = []
# Global event to signal the threads to stop
stop_event = threading.Event()

def signal_handler(signum, frame):
    print("Received signal. Stopping threads...")
    stop_threads()

def send_message_to_telegram(msg):
    telegram_integaration.send_message_to_telegram(msg)

# Function to gracefully stop all threads
def stop_threads():
    print("Stopping threads...")
    stop_event.set()

    # Print the list of phone numbers
    print("Size of Phone Numbers:")
    print(len(Number_List))
    #print("List of Phone Numbers:")
    #print(Number_List)
    time.sleep(3)
    sys.exit()

# Set up the signal handler for SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)

def read_data():
    conn = sqlite3.connect('gsm_data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM gsm_data')
    rows = c.fetchall()
    conn.close()
    return rows

data_rows = read_data()
#for row in data_rows:
#    print(row)

def create_database():
    conn = sqlite3.connect('gsm_data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS gsm_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_number TEXT,
            message_index INTEGER,
            status TEXT,
            sender TEXT,
            timestamp TEXT,
            message_content TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_data(module_number, message_index, status, sender, timestamp, message_content):
    conn = sqlite3.connect('gsm_data.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO gsm_data (
            module_number, message_index, status, sender, timestamp, message_content
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (module_number, message_index, status, sender, timestamp, message_content))
    conn.commit()
    conn.close()

def get_gsm_module_number(serial_port):
    """Retrieves the phone number of the GSM module connected to the specified serial port.

    Args:
        serial_port: The serial port object to communicate with the module.

    Returns:
        The phone number of the GSM module, or None if not found.
    """

    ser = serial_port

    ser.write(b"AT+CNUM\r")
    time.sleep(0.5)
    response = ser.readall().decode("utf-8")

    for line in response.splitlines():
        if line.startswith("+CNUM:"):
            phone_number = line.split(",")[1].replace('"', "")

            return phone_number[-10:]

    return None  # Return None if number not found

#run before scann to clear any old messages that are read.
def deleteReadMessage(ser):
    try:#it take
        #number = get_gsm_module_number(ser)
        time.sleep(2)
        # Set text mode for SMS messaging
        ser.write(b"AT+CMGF=1\r")
        time.sleep(0.5)

        ser.write(b"AT+CMGL=\"REC READ\"\r")  # all Read messages
        time.sleep(1)

        response = ser.read_all().decode("utf-8")
        for line in response.splitlines():
            if line.startswith("+CMGL:"):
                message_index = line.split(",")[0].split(":")[1]
                ser.write(b"AT+CMGD=" + message_index.encode() + b"\r")  # Delete specific message
                time.sleep(0.5)

        #print(f"module old messages are cleaned")
    except Exception as e:
        pass
        #print(f"old messages are not cleaned")

def delete_sent_sms(ser, message_index):
    try:
        time.sleep(2)
        # Delete message from GSM module
        ser.write(b"AT+CMGD=" + message_index.encode() + b"\r")
        time.sleep(0.5)

        print(f"message index # {message_index} deleted")

    except Exception as e:
        print(f"Error deleting message {message_index}: {e}")

def process_gsm_module(gsm_port):
    try:
        # Initialize serial communication
        with serial.Serial(gsm_port.name, 9600, timeout=5) as ser:
            number = get_gsm_module_number(ser)

            #print(number+"\n\r")
            if number is None:
                NOT_FOUND.append(str(gsm_port.name) + " number not found\n")
                return
            else:
                with Number_List_lock:
                    print(number, gsm_port.name)
                    Number_List.append(number)

            # Set text mode for SMS messaging
            ser.write(b"AT+CMGF=1\r")
            time.sleep(0.5)

            while True:


                # Read all messages (including unread and read)
                ser.write(b"AT+CMGL=\"REC UNREAD\"\r")
                time.sleep(1)  # Adjust timeout based on response length

                # Process response
                response = ser.read_all().decode("utf-8")

                filters = ["'AT+CMGF=1\\r\\r\\nOK\\r\\nAT+CMGL=\"REC UNREAD\"\\r\\r\\nOK'",
                           "'AT+CMGL=\"REC UNREAD\"\\r\\r\\nOK'",
                           "'AT+CMGL=\"REC UNREAD\"\\r\\r\\nOK\\r\\n\\r\\n+CMTI: \"SM\",1"]

                continueFlag = False
                for filter in filters:
                    if repr(response.strip()) == filter:
                        continueFlag = True

                pattern = r"'AT\+CMGD=\s*\d+\s*\\r\\r\\nOK\\r\\nAT\+CMGL=\"REC UNREAD\"\\r\\r\\nOK'"
                if re.match(pattern, repr(response.strip())):
                    continueFlag = True

                pattern = r"'AT\+CMGL=\"REC UNREAD\"\\r\\r\\nOK\\r\\n\\r\\n\+CMTI: \"SM\",\d+'"
                if re.match(pattern, repr(response.strip())):
                    continueFlag = True

                if continueFlag:
                    continue

                print(repr(response.strip()))

                for line in response.splitlines():
                    if line.startswith("+CMGL:"):
                        # Extract message details
                        message_index = line.split(",")[0].split(":")[1]
                        status = line.split(",")[1].replace('"', "")
                        sender = line.split(",")[2].replace('"', "")
                        timestamp = line.split(",")[4].replace('"', "")

                        # Read message content
                        ser.write(b"AT+CMGR=" + message_index.encode() + b"\r")
                        time.sleep(0.5)
                        message_content = ser.read_all().decode("utf-8")


                        if len(message_content.splitlines()) >= 3:

                            message_content = '\n'.join(message_content.splitlines()[3:-1])

                            insert_data(number, message_index, status, sender, timestamp, message_content)

                            msg = f"GSM Module Number: {number}\n" \
                                  f"Message #{message_index}:\n" \
                                  f"Status: {status}\n" \
                                  f"Sender: {sender}\n" \
                                  f"Timestamp: {timestamp}\n" \
                                  f"Content: {message_content}"

                            # Print message details
                            print(msg)
                            print("---")

                            telegramMsg = f"{number}\n\n" \
                                  f"{sender}\n" \
                                  f"{wrap_digits_in_backticks(message_content)}"

                            print(f"telegram {telegramMsg}")
                            print("sending msg....")
                            send_message_to_telegram(telegramMsg)

                            threading.Thread(target=delete_sent_sms, args=(ser, message_index)).start()
                            #th = threading.Thread(target=deleteReadMessage, args=(ser,)) # delete all read.
                            #th.start()
                            #th.join()

                    #deleteReadMessage(ser)

                # Wait for 4 seconds before reading again
                time.sleep(4)


    except Exception as e:
        print(f"Error accessing port {gsm_port.name}: {e}")

import re

def wrap_digits_in_backticks(input_string):
    # Define a regular expression pattern to match 4 to 6 digits
    pattern = re.compile(r'\b\d{4,6}\b')

    # Find all matches in the original message
    matches = pattern.findall(input_string)

    # Wrap the matches with <code> tags if not already wrapped
    for match in matches:
        code_tag = f'<code>{match}</code>'
        input_string = re.sub(r'\b' + re.escape(match) + r'\b', code_tag, input_string)

    return input_string

def showNumbers():
    time.sleep(20)
    print("NOT FOUND: ", "".join(NOT_FOUND))
    print("List of Phone Numbers:")
    #print(Number_List)
    print("FOUND: ", len(Number_List))

# Create the database table
create_database()

# Get the list of GSM ports
ports = serial.tools.list_ports.comports()
##print(f"Number of total ports: {len(ports)}")
gsm_ports = [port for port in ports if port.vid == 1250]
print(f"GSM ports: {len(gsm_ports)}")

# Create a thread for each GSM port
threads = []
for gsm_port in gsm_ports:
    thread = threading.Thread(target=process_gsm_module, args=(gsm_port,))
    threads.append(thread)

# Start all threads
for thread in threads:
    thread.start()

thread = threading.Thread(target=showNumbers)
thread.start()

# Wait for all threads to complete
for thread in threads:
    thread.join()