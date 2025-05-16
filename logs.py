from loguru import logger
import time
import sys

def logging_setup():

    format_info = "<white>[{time:YYYY-MM-DD HH:mm:ss}]</white> <level>{message}</level>"
    format_error = "<white>[{time:YYYY-MM-DD HH:mm:ss}]</white> <blue>{level}</blue> | " \
                   "<white>{name}</cyan>:<cyan>{function}</white>:<cyan>{line}</cyan> | <level>{message}</level>"

    # if sys.platform == "win32":

    logger.remove()

    logger.add(f"data/logs/{int(time.time() * 1000)}.txt", colorize=False,
               format=format_info, encoding="utf-8")

    logger.add(sys.stdout, colorize=True,
               format=format_info, level="INFO")


def clean_brackets(raw_str):
    clean_text = re.sub(brackets_regex, '', raw_str)
    return clean_text


# brackets_regex = re.compile(r'<.*?>')

logging_setup()