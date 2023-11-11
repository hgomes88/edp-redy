"""Argparser."""
import argparse

parser = argparse.ArgumentParser(description="Login into Redy")

parser.add_argument("-u", "--username", action="store", help="Username")

parser.add_argument("-p", "--password", action="store", help="Password")

parser.add_argument(
    "-upid",
    "--user_pool_id",
    action="store",
    default=None,
    help="User Pool Id",
)

parser.add_argument(
    "-cid", "--client_id", action="store", default=None, help="Client Id"
)

parser.add_argument("-r", "--region", action="store", default=None, help="Region")

parser.add_argument(
    "-iid",
    "--identity_id",
    action="store",
    default=None,
    help="Identity Id",
)

parser.add_argument(
    "-il",
    "--identity_login",
    action="store",
    default=None,
    help="Identity Login",
)
