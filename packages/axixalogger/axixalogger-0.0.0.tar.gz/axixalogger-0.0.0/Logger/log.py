RESET = '\033[0m'
error_color = {
    'ERROR' : '\033[91m',
    "WARNING" : "\033[93m",
    "INFO" : "\033[94m",
    "SUCCESS" : "\033[92m"
}




def print_logger(type,message):
    print(f"{error_color.get(type.upper(),'\033[94m')}{type}::{message}{RESET}")

