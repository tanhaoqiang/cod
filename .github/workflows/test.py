from subprocess import check_call

check_call(["pip", "install", "-U", "pip"])
check_call(["pip", "install", "-i", "https://tanhaoqiang.github.io/simple", "solv"])
check_call(["pip", "install", "."])
check_call(["python", "-munittest", "-v", "tests"])
