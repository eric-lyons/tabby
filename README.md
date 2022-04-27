# Tabby
Updated 4/25/2022

# Introduction:
Looker can send data to external sources with the built-in features such as connections to SFTP and SMTP, but we set a custom destination using [Looker Actions](https://docs.looker.com/sharing-and-publishing/action-hub). Looker Actions not only allows us to send data from Looker to custom destinations, but we can use these destinations as an extension of Looker to process data or reformat deliverables for end-users. 

This walks through how to create a Looker Action to Send tabbed Excel files from Looker to various destinations

For a full list of the open source actions, please refer to this repo. 

In this tutorial, we will go over how to send a dashboard to an email using Google Cloud Functions. 

This is designed as a framework for your development team to extend, customize, and own.  

We will use Python for this example, but you can write the action in a programming language of your choice. 

# Why Cloud Functions?

Cloud Functions are no-ops and a fully scalable service. Developers can create these and require little to no networking/SRE knowledge. The Cloud Function spins up based on events, in our case, a post from Looker. They can scale up to 3000 concurrent functions or scale down to zero when they are not in use which means you only pay for what you use. Cloud Functions also provide full logging capabilities and can be managed with traditional IAM settings. . 

For more information, feel free to try out the Cloud Functions Qwicklab found [here](https://www.qwiklabs.com/focuses/916?parent=catalog).

We are going to use three Google Cloud Functions to launch our action. 

In this example, we will use two separate cloud functions for our workflow, but you can use a single function and create multiple call back endpoints. 

For this example, please see this repo. 

Shoutout to David for helping with the authentication aspect and being a pioneer with Looker Actions. 
Setting up the Cloud Functions 
We need to make sure we enable the Cloud Run, Cloud Functions, and Cloud Storage APIs in the GCP console if they are not already enabled. 
Service Accounts
We will also create two service accounts since these APIs will be accessed by an application. We want to ensure that the service account has the correct access on both the GCS buckets and Cloud Functions. Since this is a dev environment, I gave both Service accounts owner access, but for production, please abide by the principle of least privilege and make sure your security team approves the permissions. 

# The Three Cloud Functions:
These names can be changed, but these three server integral parts of the action workflow. 

Now, we can create our cloud functions. I choose generation 1, but feel free to customize your setup. I also selected to allow unauthorized access for ease of use and the fact we are using a token adds an extra layer of security. I picked 1 GB of memory, but this will increase your bill. The memory does depend on the complexity of your function, but please test this on your own. 

Finally, I selected Python 3.8 as the runtime. 

Be sure to name your entry_point the same as your controller functions. The entry_point is how programming functions are called within the Cloud function. 


# Creating the Authentication Mechanism

To create our token we will use openssl. I used the openssl rand -base64 32 command. 

We then add this to [Google Cloud’s Secret Manager](https://cloud.google.com/secret-manager). 

The first Python function used in all the action_form and action_list is the authentication function. This function checks the header added in Looker and compares it to the secret stored in the Google Cloud’s Secret Manager. If they do not match we fail the authentication and the action will fail to complete. We talk about this in a later section, but this secret is added in the Looker UI in admin --> actions. For this example, we called the token "header". When creating the Cloud Function click Security settings and reference secret. Then, select the correct key stored in Google Cloud Secret Manager. Select Exposed as Enviromental Variable. You should also follow this process in the action_execute function, where you need to reference the project_name, the email_address for the sender and the email address password. You can access these as enviromental variables with os.environ.get('NAME').

In the other functions, we checked to make sure the authentication function worked as expected and returned a 200. 

```
def authenticate(request):
    if request.method != 'POST':
        r =  '|ERROR| Request must be POST'; print (r)
        return Response(r, status=401, mimetype='application/json')

    elif 'authorization' not in request.headers:
        r = '|ERROR| Request does not have auth token'; print (r)
        return Response(r, status=400, mimetype='application/json')

    else:
        # header is the name of the secret saved in Cloud Secret Manager
        expected_auth_header = 'Token token="{}"'.format(os.environ.get('header'))
        submitted_auth = request.headers['authorization']
        if hmac.compare_digest(expected_auth_header,submitted_auth):
            return Response(status=200, mimetype='application/json')

        else:
            r = '|ERROR| Incorrect token'; print (r)
 ```
 

# action_form

In action_form we defined a function called, you guessed it, action_form. It accepts the json payload as an argument. We define a response here which is the form fields users see in the Looker UI, when they select the action. 
 
 ```
def action_form(request):
    auth = authenticate(request)
    if auth.status_code != 200:
        return auth

    response = [
  {"name": "bucket", "label": "GCS Bucket Name", "type": "string"},
  {"name": "subject_name", "label": "Subject Name", "type": "string"},
  {"name": "email", "label": " email address", "type": "string"}
      ]

    print ('returning form json')
    return json.dumps(response)
```

The only thing the form needs to do is return the response as JSON is the authentication function returns a 200. 

# action_execute 

The second cloud function we create is called action_execute. This is the meat and potatoes of Looker Actions. It is where we do the heavy lifting. Here we define a function called execute and set that as our entry point. We call the other functions from execute. Execute accepts response as an arg. From here, you can define your own functions, using whichever Python Libraries you would like. We can transform the data from Looker and send it to another destination. 

I develop these locally and use pip freeze to show all the package versions needed for the requirements.txt file. 

For further reading on the requirements.txt file, please see this link. 

In our example, we created a function called email using the yagamail library to send our end user the payload. We are again using the Google Secret Manager to store the application password to the email. I would suggest using a production grade SMTP service such as SendGrid or Sailthru. 


# action_list

Our last cloud function is action_list. Here we define a function called, action_complete and reuse the authentication function from action_form. 
The entry point is again set to action_complete.

The main purpose of this function is to return a response when called by the Looker action API. We define the action name, we add the URI of our icon, we define the supported action types, supported formats, and specify the form_url and url. The form_url points at the trigger for action_form which we saved in a txt file in the earlier steps and the url points to the trigger for the action_execute function which we just defined. 

To create the URI we used this [open-source tool](https://onlinepngtools.com/convert-png-to-data-uri). 

```
def action_list(request):
    auth = authenticate(request)
    if auth.status_code != 200:
        return auth
    """Return a list of actions"""
    return {
       "label": "Send Tabbed Dashboards with Tabby!",
       "integrations": [
           {
           "name": "Tabby",
           "label": "Tabby",
           "description": "Write dashboard tiles to a tabbed excel sheet.",
           "form_url":"https:FUNCTIONURLGOESHERE/action_form",
           "supported_action_types": ["dashboard"],
           "supported_download_settings": ["url"],
           "supported_formats": ["csv_zip"],
           "supported_formattings": ["unformatted"],
           "url": "https:FUNCTIONURLGOESHERE/action_execute",
           "icon_data_uri": URIGOESHERE"

           }
       ]
    }
```
 
# Alternative Options

If you decide to use your own server, you will need to create url endpoints to call each of these functions. You will also need to ensure your allowlist settings allow traffic from Looker to pass through the firewall. 
 
Alternatively, if you create your own action, you can attempt to submit a request to the main looker actions repo to have the action enabled on the Looker Action Hub infrastructure. While this allows other Looker customers to leverage your action, it does remove your ability to control the network settings and scale of the instances the action(s) run on. 

# Adding the Action to Looker
To add the action in Looker, an admin needs to go to Admin → Actions. Scroll to the bottom of the page and select Add Action Hub. Add the action url which you can find by selecting the action_execute Cloud Function and selecting trigger. Once the url is added, then add the secret generated in the earlier section. Save these settings!

# Testing the Action with Beeceptor 

[Beeceptor](https://beeceptor.com/) is a tool to intercept API calls and inspect the object. It is a free service. Feel free to use another resource if there is a preferred method. 

To test the payload sent from Looker to our Cloud Function, we replace the url parameter in action_complete with the Beeceptor link. This will send the expected payload to Beecepter where we can inspect the shape and contents. This is key to customizing the action_execute function. It also allows us to understand how the parameters from the action_form object are passed over in the final payload format. 
 
You can also use this payload in the Cloud Function testing functionality to manually pass in the payload rather than have to resent it through Looker. This is extremely useful if the query runtime for the desired schedules take a long time or is resource intensive. 

# More Resources:
https://github.com/davidtamaki/looker-custom-action-content-manager

https://docs.looker.com/sharing-and-publishing/action-hub

https://training.looker.com/the-action-hub

https://github.com/looker-open-source/actions

https://github.com/looker-open-source/actions/blob/master/docs/action_api.md


