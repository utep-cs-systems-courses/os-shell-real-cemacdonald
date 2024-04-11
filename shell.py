#! /usr/bin/env python3

import os,re,readline,sys

def run_command(command):
    try:
        os.execve(command[0], command, os.environ)
    except FileNotFoundError:
        pass

    for directory in re.split(":", os.environ['PATH']):
        program = f"{directory}/{command[0]}"
        try:
            os.execve(program, command, os.environ)
        except FileNotFoundError:
            pass
    os.write(2, f"{command[0]}: Command not found\n".encode())
    exit(1)

def pipes(command):
    index = command.index('|')
    left_side = command[:index]
    right_side = command[index + 1:]

    pipe_reader, pipe_writer = os.pipe()

    rc = os.fork()
    if rc < 0:
        exit(1)
    elif rc == 0:
        os.close(1)  # Close standard output
        os.dup(pipe_writer)  # Duplicate pipe writer to standard output
        os.set_inheritable(1, True)
        os.close(pipe_reader)
        os.close(pipe_writer)
        run_command(left_side)
    else:
        os.close(0)  # Close standard input
        os.dup(pipe_reader)  # Duplicate pipe reader to standard input
        os.set_inheritable(0, True)
        os.close(pipe_reader)
        os.close(pipe_writer)
        run_command(right_side)

def redirection(command):
    if '>' in command:
        index = command.index('>')
        output_file = command.pop(index + 1)
        command.pop(index)
        os.close(1)  # Close standard output
        os.open(output_file, os.O_CREAT | os.O_WRONLY)
        os.set_inheritable(1, True)
        return True

    if '<' in command:
        index = command.index('<')
        input_file = command.pop(index + 1)
        command.pop(index)
        os.close(0)  # Close standard input
        os.open(input_file, os.O_RDONLY)
        os.set_inheritable(0, True)
        return True
    return False

def main():
    while True:
        prompt = os.getenv('PS1', '$ ')
        print(prompt, end='', flush=True)
        command = input().strip()
        
        if command == '':
            print()
            continue
        
        if command.lower() == 'exit':
            exit(0)

        command = list(filter(None, command.split(' ')))
        
        if command[0].lower() == 'cd':
            if len(command) >= 2:
                if command[1] == '..':
                    os.chdir('..')
                else:
                    try:
                        os.chdir(command[1])
                    except FileNotFoundError:
                        os.write(2, f"bash: cd: {command[1]}: No such file or directory\n".encode())
            else:
                os.chdir(os.environ['HOME'])
            continue
        
        rc = os.fork()
        wait = True
        if command[-1] == '&':
            wait = False
            command.pop()
        if rc < 0:
            exit(1)
        elif rc == 0:
            if '|' in command:
                pipes(command)
            elif '>' in command or '<' in command:
                if not redirection(command):
                    os.write(2, "Invalid redirection\n".encode())
                    continue
            run_command(command)
        else:
            if wait:
                os.wait()

if __name__ == "__main__":
    main()
