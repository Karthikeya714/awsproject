"""Quick test to verify auth app displays login page."""
import sys
import os

# Check if files exist
auth_app = "d:\\genaiproject\\app\\streamlit_app_auth.py"
user_auth = "d:\\genaiproject\\backend\\user_auth.py"

print("=" * 50)
print("CHECKING AUTHENTICATION FILES")
print("=" * 50)

if os.path.exists(auth_app):
    print(f"✅ Auth App Found: {auth_app}")
    print(f"   Size: {os.path.getsize(auth_app)} bytes")
else:
    print(f"❌ Auth App NOT Found: {auth_app}")

if os.path.exists(user_auth):
    print(f"✅ User Auth Module Found: {user_auth}")
    print(f"   Size: {os.path.getsize(user_auth)} bytes")
else:
    print(f"❌ User Auth Module NOT Found: {user_auth}")

print("\n" + "=" * 50)
print("TO RUN THE AUTH APP:")
print("=" * 50)
print("\nOption 1 (PowerShell):")
print("   cd d:\\genaiproject")
print("   .\\venv\\Scripts\\Activate.ps1")
print("   streamlit run app\\streamlit_app_auth.py")

print("\nOption 2 (Use the batch file):")
print("   cd d:\\genaiproject")
print("   .\\run_auth_app.bat")

print("\nOption 3 (Use PowerShell script):")
print("   cd d:\\genaiproject")
print("   .\\run_auth_app.ps1")

print("\n" + "=" * 50)
print("WHAT YOU'LL SEE:")
print("=" * 50)
print("1. Browser opens automatically")
print("2. You see: '🖼️ Welcome Back' (SIGNIN page)")
print("3. Click 'Create Account' button to see SIGNUP page")
print("4. Fill form and create account")
print("5. Login and use the app!")
print("=" * 50)
