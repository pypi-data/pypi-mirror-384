import logging
import sys

# logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s:%(message)s')
red = "\033[31m"
green = "\033[32m"
end = "\033[00m"
dark_green = "\033[92m"

formatter = logging.Formatter(
    f"{red}%(asctime)s - %(name)s{end} :: {green}%(levelname)s - %(message)s{end}"
)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)

logger.setLevel("INFO")
logger.addHandler(handler)
