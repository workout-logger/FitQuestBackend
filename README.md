## Prerequisites

1. **Python** (3.8 or above) with `pip`
2. **Django** (Install via `pip install django`)
3. **Ngrok** (Download from [ngrok.com](https://ngrok.com/download))

---

```bash
# Clone the repository
git clone <repository-url>
cd <repository-folder>

# Install required dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py makemigrations
python manage.py migrate

# Create a superuser (optional, for admin access)
python manage.py createsuperuser

# Run the Django server
python manage.py runserver

# Create a fixed domain on ngrok https://dashboard.ngrok.com/domains

# Expose the server using Ngrok
ngrok http --domain=[CUSTOM DOMAIN HERE] 8000

# Lastly run the frontend with flutter
flutter run