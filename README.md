# Phishing Simulation Application

A web application for educational phishing simulations, designed to raise awareness about phishing attacks.

## Features

- Simulated Google login page
- Admin dashboard to view captured credentials
- Educational content about phishing awareness
- Statistics tracking

## Setup

1. Clone the repository:
```
git clone https://github.com/pasta-lover69/phish-sim.git
cd phish-sim
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Install Prisma:
```
pip install prisma
```

4. Set up environment variables by editing the `.env` file:
```
DATABASE_URL="postgresql://username:password@localhost:5432/phish_sim"
SECRET_KEY="your-secure-secret-key"
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="your-secure-admin-password"
```

5. Set up the database:
```
prisma db push
python setup_db.py
```

## Running the Application

```
flask run
```

The application will be available at `http://localhost:5000`.

## Admin Access

Access the admin panel at `http://localhost:5000/admin_login` with the credentials specified in your `.env` file.

## Deployment

This application is configured for deployment on Vercel using the provided `vercel.json` configuration.

## Important Note

This application is for educational purposes only. Do not use it for malicious activities. 