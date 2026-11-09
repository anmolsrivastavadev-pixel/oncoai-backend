#!/usr/bin/env python
"""Create a user with a role, or change an existing user's role.

    python scripts/create_admin.py someone@example.com --role moderator
"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402
from app.models.enums import Role  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email")
    parser.add_argument("--role", choices=[r.value for r in Role], default=Role.admin.value)
    parser.add_argument("--name", default="OncoAI Admin")
    args = parser.parse_args()
    email = args.email.strip().lower()

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            password = getpass.getpass("Password for new user: ")
            if len(password) < 8:
                print("Password must be at least 8 characters.", file=sys.stderr)
                return 1
            user = User(email=email, full_name=args.name, hashed_password=hash_password(password))
            db.add(user)
        user.role = Role(args.role).value
        db.commit()
        print(f"{email} now has role {args.role}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
