# scripts/clean_hierarchy.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import State, Region, OldGroup, Group, District, User

def clean_hierarchy():
    """Completely wipe all hierarchy data and associated users"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🧹 Starting hierarchy cleanup...")
            
            # Count records before deletion
            states_count = State.query.count()
            old_groups_count = OldGroup.query.count()
            groups_count = Group.query.count()
            districts_count = District.query.count()
            
            print(f"📊 Current counts - States: {states_count}, OldGroups: {old_groups_count}, Groups: {groups_count}, Districts: {districts_count}")
            
            # Delete in correct order to handle foreign key constraints
            print("🗑️  Deleting districts...")
            District.query.delete()
            
            print("🗑️  Deleting groups...")
            Group.query.delete()
            
            print("🗑️  Deleting old groups...")
            OldGroup.query.delete()
            
            print("🗑️  Deleting regions...")
            Region.query.delete()
            
            print("🗑️  Deleting states...")
            State.query.delete()
            
            # Delete group users (users with email containing @thedcmp.org)
            print("🗑️  Deleting group users...")
            group_users = User.query.filter(User.email.like('%@thedcmp.org')).all()
            for user in group_users:
                db.session.delete(user)
                print(f"   Deleted user: {user.email}")
            
            db.session.commit()
            
            print("✅ Hierarchy cleanup completed successfully!")
            print("📊 Final counts:")
            print(f"   States: {State.query.count()}")
            print(f"   OldGroups: {OldGroup.query.count()}")
            print(f"   Groups: {Group.query.count()}")
            print(f"   Districts: {District.query.count()}")
            print(f"   Group users: {User.query.filter(User.email.like('%@thedcmp.org')).count()}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Cleanup failed: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    confirm = input("⚠️  This will DELETE ALL hierarchy data and group users. Type 'YES' to confirm: ")
    if confirm == "YES":
        clean_hierarchy()
    else:
        print("❌ Cleanup cancelled.")