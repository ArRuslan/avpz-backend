import itertools

import bcrypt

from hhb.models import User, UserRole, Hotel, HotelAdmin, Room

BCRYPT_DEFAULT_HASH = bcrypt.hashpw(b"asdQwe123):", bcrypt.gensalt(5)).decode("utf8")
BULK_COUNT = 64

ROLES = (UserRole.USER, UserRole.BOOKING_ADMIN, UserRole.ROOM_ADMIN, UserRole.HOTEL_ADMIN, UserRole.GLOBAL_ADMIN)
MFA_KEY = (None, "A" * 16)

async def create_test_data():
    for role, mfa_key in itertools.product(ROLES, MFA_KEY):
        phone_digit = "0"
        email_name = f"test_user.{role.name.lower()}"
        if mfa_key is not None:
            email_name += ".mfa"
            phone_digit = "1"

        await User.bulk_create([
            User(
                email=f"{email_name}.{i}@example.com",
                password=BCRYPT_DEFAULT_HASH,
                first_name="Test",
                last_name="User",
                phone_number=f"+38099{phone_digit}{str(role.value).zfill(3)}{str(i).zfill(3)}",
                role=role,
            )
            for i in range(BULK_COUNT)
        ])

        print(f"Created {BULK_COUNT} users with role {role} and mfa key {mfa_key!r}")

    await Hotel.bulk_create([
        Hotel(
            name=f"Hotel {i}",
            address=f"Some city, some street {i}",
            description=f"Test hotel {i}",
        )
        for i in range(BULK_COUNT)
    ])

    print(f"Created {BULK_COUNT} hotels")


    for hotel in await Hotel.all():
        await Room.bulk_create([
            Room(
                hotel=hotel,
                type="some_type_idk",
                price=50 * i
            )
            for i in range(BULK_COUNT)
        ])
        print(f"Created {BULK_COUNT} rooms in hotel {hotel.id}")

    for idx, hotel in enumerate(await Hotel.all()):
        for role in ROLES[1:-1]:
            admins_count = await User.filter(role=role).count()
            admins_per_hotel = int(admins_count / BULK_COUNT)
            admins = await User.filter(role=role).limit(admins_per_hotel).offset(idx * admins_per_hotel)
            await HotelAdmin.bulk_create([
                HotelAdmin(hotel=hotel, user=admin)
                for admin in admins
            ])

            emails = ", ".join([admin.email for admin in admins])
            print(f"Added {len(admins)} admins ({emails}) to hotel {hotel.id}")
