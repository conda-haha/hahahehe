"""ReAct prompt constants for InterCode — verbatim copy from G.O.D eval_intercode.py.

Keeping these in sync with the evaluator ensures training data format matches
the exact prompt structure the model sees at eval time.
"""

OBS_TRUNCATE_CHARS = 350  # matches eval_intercode.py DEFAULT_OBS_TRUNCATE_CHARS

REACT_INIT_MSG = """Interact with a Bourne Shell system using Bash queries to answer a question.
Use interleaving Thought, Action, Observation steps.
Thought can reason about the current situation, and Action can be two types:
(1) execute, which executes Bash code on the Bourne Shell system
(2) submit, which indicates that the previous observation is the answer
Here are some examples.
"""

DEMO_BASH_REACT = """Question: Convert the first 16 characters in "/testbed/textfile7.txt" to a single hexadecimal value
Thought 1: I can use the `xxd` command to get a hexdump of the /textbed/textfile7.txt file
Action 1: execute[xxd -p -l 16 /testbed/textfile7.txt]
Observation 1: /bin/bash: line 1: xxd: command not found
Thought 2: Seems like xxd is not available. I can try to use `od` (octal dump) command to get a hexadecimal dump.
Action 2: execute[od -A n -t x1 -N 16 /testbed/textfile7.txt]
Observation 2:  54 65 78 74 20 66 69 6c 65 20 37 20 77 69 74 68
Thought 3: This command is showing the hexadecimal representation of the first 16 bytes, but it is not a single value.
I should try stitching together the values into one continuous string.
Action 3: execute[od -A n -t x1 -N 16 /testbed/textfile7.txt | awk '{$1=$1;print}' | tr -d ' ']
Observation 3: 546578742066696c6520372077697468
Thought 4: I've configured
Action 4: submit
Question: Calculate a list of duplicate md5 sum hashes for all the ".java" files in the /testbed directory
Thought 1: Find all files with the `.java` extension in `testbed/`, then calculate the md5hash, sort them,
filter out duplicates, and only pick the first line of the hash.
Action 1: execute[find /testbed -name "*.java" -type f -exec md5sum {} + | sort | uniq -d | cut -d' ' -f1]
Observation 1:
Thought 2: Seems like this did not produce any results. I may have to use another command instead of cut
to pick out the hashes from the output string
Action 2: execute[find /testbed -name "*.java" -type f -exec md5sum {} + | sort | uniq -Dw 32]
Observation 2: f32a3a97638afeb2ee2a15cfe335ab72  /testbed/Hello.java
f32a3a97638afeb2ee2a15cfe335ab72  /testbed/Hello1.java
f32a3a97638afeb2ee2a15cfe335ab72  /testbed/dir1/AnotherHello.java
Thought 3: This shows the output hashes and they have the same values, indicating that these files are duplicates.
However, the file names are also shown, which are not needed.
Action 3: execute[find /testbed -name "*.java" -type f -exec md5sum {} + | sort | uniq -D -w 32 | cut -c 35-]
Observation 3: /testbed/Hello.java
/testbed/Hello1.java
/testbed/dir1/AnotherHello.java
Thought 4: This shows the file names exclusively, and no longer shows the hashes. It seems that the cut
command argument may not be the best choice for selecting file names.
Action 4: execute[find /testbed -name "*.java" -type f -exec md5sum {} + | sort | uniq -D -w 32 | awk '{print $2}']
Observation 4: /testbed/Hello.java
/testbed/Hello1.java
/testbed/dir1/AnotherHello.java
Thought 5: I use the awk command instead, but instead of printing out the hashes, it still prints out the file
names. I should select a different part of the output string instead of `$2`
Action 5: execute[find /testbed -name "*.java" -type f -exec md5sum {} + | sort | uniq -D -w 32 | awk '{print $1}']
Observation 5: f32a3a97638afeb2ee2a15cfe335ab72
f32a3a97638afeb2ee2a15cfe335ab72
f32a3a97638afeb2ee2a15cfe335ab72
Thought 6: This prints out identical hashes, and based on previous observations, I know that these are hashes of
duplicates `.java` files from the `testbed/` directory. This should be correct. I will submit.
Action 6: submit
Question: print disk usage in human readable format of files or folders in /workspace
Thought 1: The `du` command is useful for printing out disk usage of a specific directory. I can use this to
display this information for the `workspace` directory
Action 1: execute[du /workspace]
Observation 1: 48\t/workspace/dir1
8\t/workspace/dir2/mysql
24\t/workspace/dir2
100\t/workspace
Thought 2: The default `du` command gives storage in a non-human readble font. I can use the -h option
of the du command to print storage size with bytes.
Action 2: execute[du -h /workspace]
Observation 2: 48K\t/workspace/dir1
8.0K\t/workspace/dir2/mysql
24K\t/workspace/dir2
100K\t/workspace
Thought 3: This gives me storage information for every folder under the workspace directory, but
I only need the storage for just the `workspace/` directory. The `-s` option should help with this.
Action 3: execute[du -sh /workspace]
Observation 3: 100K\t/workspace
Thought 4: This shows data usage in human readable format for the `workspace` directory. I am finished.
Action 4: submit
Question: Count all the lines of all php files in the /testbed directory recursively
Thought 1: I should find the paths to all php files in the testbed directory, then apply the word
count command to each path.
Action 1: execute[find /testbed -name "*.php" | xargs wc -l]
Observation 1:  1 /testbed/dir1/info.php
 1 /testbed/hello.php
 2 total
Thought 2: This shows me too much information, I only need the total number of lines. I should add up
the lines together and output a single number.
Action 2: execute[find /testbed -name "*.php" -exec wc -l {} + | awk '{total += $1} END{print total}']
Observation 2: 4
Thought 3: This total is wrong, it doesn't match the previous observation, where total is 2. I only
need to apply the word count command.
Action 3: execute[find /testbed -name "*.php" -type f -exec cat {} + | wc -l]
Observation 3: 2
Thought 4: The value is 2, which matches the initial observation that the total lines of php files in the
testbed directory is 2. I can submit.
Action 4: submit
Question: Create a hello.txt file in the /testbed directory and add the text "Hello world" to it.
Thought 1: I can first create a `hello.txt` file in the `testbed/` directory
Action 1: touch testbed/hello.txt
Observation 1:
Thought 2: I should check that the file was created successfully.
Action 2: execute[ls testbed/]
Observation 2: dir1/
dir2/
dir3/
hello.txt
files.txt
Thought 3: I can now add the "Hello world" text to the hello.txt file
Action 3: execute[echo Hello world > hello.txt]
Observation 3:
Thought 4: I should check that the text was written successfully to the hello.txt file.
Action 4: execute[cat testbed/hello.txt]
Observation 4: Hello world
Thought 5: The hello.txt file has been created successfully in the testbed/ directory, and it contains
the Hello World text. I can submit.
Action 5: submit
"""


def build_step_prompt(
    query: str,
    history: list[tuple[str, str, str]],
    turn: int,
) -> str:
    """Build the user message that the evaluator sends for turn N of a ReAct episode.

    Args:
        query:   the NL2Bash question (e.g. "Count all .php files…")
        history: list of (thought, action, observation) for completed turns 1..N-1
        turn:    the turn number being predicted (1-based)

    Returns:
        Full accumulated prompt ending with "Thought {turn}:", matching exactly
        what eval_intercode._run_react_episode() sends to the model.
    """
    prompt = REACT_INIT_MSG + DEMO_BASH_REACT + f"Question: {query}\n"
    for i, (thought, action, obs) in enumerate(history, 1):
        obs_t = obs[:OBS_TRUNCATE_CHARS] if len(obs) > OBS_TRUNCATE_CHARS else obs
        prompt += f"Thought {i}: {thought}\nAction {i}: {action}\nObservation {i}: {obs_t}\n"
    prompt += f"Thought {turn}:"
    return prompt
