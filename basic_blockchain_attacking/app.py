import hashlib
import secrets
import pyotp
import qrcode
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import timedelta
from io import BytesIO
import base64

# Flask app initialization
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Set a default secure secret key (will be overridden later)

# Set session lifetime to 2 minutes
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=2)

# In-memory storage (replace with a database in production)
registered_users = {}  # {voter_id: {'name': ..., 'dob': ..., 'has_voted': False, 'hotp_secret': ...}}
vote_counts = {'Candidate A': 0, 'Candidate B': 0, 'Candidate C': 0}  # Dummy candidates

def generate_voter_id():
    # Generate a random voter ID using secrets (to ensure randomness and security)
    return secrets.token_hex(6)  # 12-character random string for Voter ID

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        dob = request.form.get('dob')

        # Automatically generate a Voter ID
        voter_id = generate_voter_id()

        if voter_id not in registered_users:
            # Register the user (normally, you would store this in a database)
            hotp_secret = pyotp.random_base32()  # Generate a random HOTP secret
            registered_users[voter_id] = {'name': name, 'dob': dob, 'hotp_secret': hotp_secret, 'has_voted': False}

            # Store voter ID in session
            session['voter_id'] = voter_id
            session.permanent = True  # Make the session permanent (apply session timeout)

            return redirect(url_for('register_success'))  # Redirect to success page after registration

    return render_template('register.html')

@app.route('/register_success', methods=['GET', 'POST'])
def register_success():
    # Get the voter_id from the session
    voter_id = session.get('voter_id')

    if not voter_id or voter_id not in registered_users:
        return redirect(url_for('register'))

    user = registered_users[voter_id]
    name = user['name']
    dob = user['dob']
    hotp_secret = user['hotp_secret']

    # Generate the OTP URI for the QR code
    totp = pyotp.TOTP(hotp_secret)
    uri = totp.provisioning_uri(f"voting_app:{voter_id}", issuer_name="VotingApp")

    # Create QR code for OTP
    img = qrcode.make(uri)

    # Convert the image to a base64 string to embed in HTML
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    img_base64 = base64.b64encode(img_io.read()).decode()

    return render_template('register_success.html', voter_id=voter_id, img_base64=img_base64)

@app.route('/login', methods=['GET', 'POST'])
def login():
    qr_code_base64 = None

    if request.method == 'POST':
        voter_id = request.form.get('voter_id')
        otp = request.form.get('otp')  # Collect OTP input (not used for verification in this case)

        # Check if the voter ID is in the registered users
        if voter_id in registered_users:
            # Check if the user has already voted
            if registered_users[voter_id].get('has_voted', False):
                return redirect(url_for('result'))  # Redirect to results page if already voted
            
            # Store voter ID in session for authentication
            session['voter_id'] = voter_id
            return redirect(url_for('vote'))  # Redirect to voting page

        # If voter ID is not registered, redirect to the registration page
        return redirect(url_for('register'))

    # Check if a voter is logged in
    voter_id = session.get('voter_id')
    if voter_id and voter_id in registered_users:
        hotp_secret = registered_users[voter_id]['hotp_secret']
        totp = pyotp.TOTP(hotp_secret)
        uri = totp.provisioning_uri(f"voting_app:{voter_id}", issuer_name="VotingApp")

        # Generate the QR code
        img = qrcode.make(uri)
        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        qr_code_base64 = base64.b64encode(img_io.read()).decode()

    return render_template('login.html', qr_code_base64=qr_code_base64)

@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if 'voter_id' not in session:
        # If not logged in, redirect to login page
        return redirect(url_for('login'))

    voter_id = session['voter_id']

    # Check if the voter has already voted
    if registered_users[voter_id].get('has_voted', False):
        return redirect(url_for('result'))  # Redirect to results page if already voted

    if request.method == 'POST':
        # Get the vote from the form (for simplicity, using candidate names as vote options)
        selected_candidate = request.form.get('candidate')
        
        if selected_candidate:
            # Increment the vote count for the selected candidate
            if selected_candidate in vote_counts:
                vote_counts[selected_candidate] += 1

            # Mark the voter as having voted
            registered_users[voter_id]['has_voted'] = True

            # Redirect to the results page after voting
            return redirect(url_for('result'))

    return render_template('vote.html', voter_id=voter_id, vote_counts=vote_counts)

@app.route('/result')
def result():
    # Display the voting results here
    return render_template('result.html', vote_counts=vote_counts)

if __name__ == '__main__':
    app.run(debug=True)

