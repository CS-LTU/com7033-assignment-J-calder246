# com7033-assignment-J-calder246

About app
This app is for users to view medical data through a secure login. One the patient view they can also update their login details and go to the contact page where they can contact the admins.

This app also has features for admins.
Admins can utilise the CRUD features of the app.
-They can create user data in the create page
-They can go to the read page where (once it loads) they can view all user records. To search for specific data (ie id) I use CTRL+G and search it that way.
From the read page there is an actions panel, which contains links to update and delete the data. The delete feature will delete the medical data from MongoDB aswellas the login details stored in sqlite.

IMPORTANT
If you wish to use the admin feature for this app the details are
LOGIN
username: Applebee
password: AdminPass42069

When registering as a normal user, please use an id from the mongoDB table or you will not be able to see any medical data e.g. 58202

CODE EXPLAINED
This application uses a modular design with several files containing python code. This is for the purposes of organisation when programming and editing the code. These files include

app4.py: Contains rountes for admins and users
apptest.py: Tests that the home, login and registration pages are working 
bootstrap.py: 
config.py: Sets up directory, path to sql datebase, creates a secret key for flask and sets up mongoDB uri and collections. Turns all these features into one fuction (Config)
db_sqlite.py: Creates MongoDB database with username, customer_id (same as id in mongo), password and confirm password
decorators.py: Sets up code that checks if a user or admin is logged in so that logging in is required to access these pages 
run.py: code to run the app
services_admin.py: Defines if and ID is an admin's, so admins can properly log in to the admin section
services_logging.py: Sets up a logging collection in MongoDB db which records log ins (and whether a admin or user logged in) and records ids

TEMPLATES DESCRIPTION
_____________________
PRE-LOGIN

Home: (/) first page that loads, links to login, registration and contact
Registration: Gets user to enter a Username, id (stored as customer id in sqlite table, used to link user account to MongoDB database and so that the admin delete function deletes login details and medical data() password and confirm password. Username must be unique, and passwords must match.
Login: Requests user username and password so they can log in
Contact: Contains a phone number and email for users to contact the site administration

USER PAGES
Profile: The first link after coming from the login. Contains various page directions  aswellas a section for chaning login details: new username, new password (with confirm password input)
patient: Matches users 'customer_id' with the id (not objectid) in MongoDB so users and retrieve and view their health data

ADMIN PAGES

Dashboard: First page admin sees after logging in, contains links for creating and reading data
Create: Requests all data required by mongoDB collection and creates a user based on that information
Read: Contains a table with all values on it. Has a bar which provides links to delete or up date the information
Update: Allows admin to change the data.

BASE PAGES (base and base_admin)
Contains base templates for use on other pages. Has a separate admin and user base with different headers and different hyperlinks.



Tests

I have ran tests to checks if various pages work by loading the page and getting it to check if various pieces of text appear. Those pages are:
Home page (page you get before login)
Registration page
Login page
All of these tests have been confirmed


Where to run
As of time of writing, prgram is running on...
https://urban-computing-machine-wrqg77q7r4vphqwj-5211.app.github.dev/ 


HOW I SEE IT WORKING

When you see you doctor, they or the hospital by email will give you your id for the account. Now you can sign in. The admin will create health data for that id so users can view their health information through the site.

