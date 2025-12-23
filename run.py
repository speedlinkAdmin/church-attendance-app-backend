from app import create_app
from app.extensions import db
from app.models.user import User, Role, Permission
import click
from flask.cli import with_appcontext
import os

app = create_app()

@app.cli.command("create-admin")
@click.option("--email", prompt=True)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
@click.option("--name", default="")
@with_appcontext
def create_admin(email, password, name):
    """Create an admin user."""
    if User.query.filter_by(email=email).first():
        print("User exists")
        return
    admin_role = Role.query.filter_by(name="admin").first()
    if not admin_role:
        admin_role = Role(name="admin", description="Full system administrator")
        db.session.add(admin_role)
        db.session.commit()
        print("Created role: admin")

    user = User(email=email, name=name)
    user.set_password(password)
    user.roles.append(admin_role)
    db.session.add(user)
    db.session.commit()
    print("Admin created:", email)

@app.cli.command("bootstrap-roles")
@with_appcontext
def bootstrap_roles():
    """Create proper roles for the hierarchy system."""
    roles = {
        "Super Admin": "Full system administrator with access to everything",
        "State Admin": "Administrator for a specific state", 
        "Region Admin": "Administrator for a specific region",
        "District Admin": "Administrator for a specific district",
        "Group Admin": "Administrator for a specific group",
        "Viewer": "Read-only access"
    }

    for role_name, description in roles.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=description)
            db.session.add(role)
            print(f"Created role: {role_name}")
    
    db.session.commit()
    print("Bootstrap complete - roles created:")
    for role in Role.query.all():
        print(f"  - {role.name}: {role.description}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    # app.run()
