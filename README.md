## Facebook Messenger Visualization

## Setup Instructions

### Installation
1. Navigate to 
```bash 
./fb_message_visualization
```
2. Using python3.6 or higher, set up the virtual environment
```bash
python -m venv venv;
source venv/bin/activate;
pip install -r requirements
```

### Requesting message data from Facebook

Facebook provides users with the ability to download historical information associated with their account.
This script makes use of historical message information. 
To recover this information from Facebook, follow the below steps:

1. Navigate to 
```https://www.facebook.com/dyi/?referrer=yfi_settings```
2. Click **Deselect All** on the **Your Information** pane, then check the box to the right of **Messages**.
3. Click **Create File** under the **Request Copy** pane.
4. It will take Facebook a while to generate this file.
Once you have it, it should be a zipped file with a name in the following format:
```facebook_<username>.zip```
5. Unzip this file and move it to the ```./fb_message_visualization``` directory.

### Processing the data

The operations of the script can be thought of in three phases:
1. Compute the temporal range in which all conversations have occurred. 
2. Divide this range into bins of uniform size (i.e., one bin for each day).
3. For each conversation thread with an individual, count the number of exchanged messages occurring in each bin.
4. Compute a 4-month moving average over the message counts in these bins.
5. Produce a csv file that is compliant with Flourish.

To run the script execute:
```bash
python fb_to_ts.py --name="<your_name_on_facebook>" --base-dir="./<name_of_messages_directory>"
```
which will produce a CSV file titled ```scores.csv```. 

### Loading the data onto Flourish
1. Go to the url ```https://public.flourish.studio/visualisation/2439541/```
2. Click **Duplicate and edit** to copy the project.
3. Click the **Data** tab above the visualization.
4. Click **Upload data** and select the scores.csv file.




