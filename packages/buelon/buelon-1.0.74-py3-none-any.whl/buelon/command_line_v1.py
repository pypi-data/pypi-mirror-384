import argparse
import os
import json
import sys
import time
import uuid
import asyncio
import logging

import dotenv
dotenv.load_dotenv(os.environ.get('ENV_PATH', '.env'))

# Import necessary modules from buelon
import buelon as pete


def delete_last_line():
    sys.stdout.write("\033[F")
    sys.stdout.write("\033[K")


def run_hub(args):
    # Set environment variables for hub
    if args.binding:
        os.environ['PIPELINE_HOST'], os.environ['PIPELINE_PORT'] = args.binding.split(':')

    if args.bucket_binding:
        os.environ['BUCKET_CLIENT_HOST'], os.environ['BUCKET_CLIENT_PORT'] = args.bucket_binding.split(':')

    # Set PostgreSQL environment variables if provided
    if args.postgres:
        os.environ['POSTGRES_HOST'], os.environ['POSTGRES_PORT'], os.environ['POSTGRES_USER'], os.environ['POSTGRES_PASSWORD'], os.environ['POSTGRES_DATABASE'] = args.postgres.split(':')

    # Run the hub
    pete.hub.main()


def run_worker(args):
    # Set environment variables for worker
    if args.binding:
        os.environ['PIPE_WORKER_HOST'], os.environ['PIPE_WORKER_PORT'] = args.binding.split(':')

    if args.bucket_binding:
        os.environ['BUCKET_CLIENT_HOST'], os.environ['BUCKET_CLIENT_PORT'] = args.bucket_binding.split(':')

    # Set PIPE_WORKER_SUBPROCESS_JOBS environment variable if provided
    if args.subprocess_jobs:
        os.environ['PIPE_WORKER_SUBPROCESS_JOBS'] = args.subprocess_jobs

    # Set PIPE_WORKER_SCOPES environment variable if provided
    if args.scopes:
        os.environ['PIPE_WORKER_SCOPES'] = args.scopes

    # Set PostgreSQL environment variables if provided
    if args.postgres:
        os.environ['POSTGRES_HOST'], os.environ['POSTGRES_PORT'], os.environ['POSTGRES_USER'], os.environ['POSTGRES_PASSWORD'], os.environ['POSTGRES_DATABASE'] = args.postgres.split(':')

    # Run the worker
    pete.worker.main(args.all)


def run_test(args):
    # Set environment variables for worker
    if args.binding:
        os.environ['PIPE_WORKER_HOST'], os.environ['PIPE_WORKER_PORT'] = args.binding.split(':')

    if args.bucket_binding:
        os.environ['BUCKET_CLIENT_HOST'], os.environ['BUCKET_CLIENT_PORT'] = args.bucket_binding.split(':')

    # Set PIPE_WORKER_SUBPROCESS_JOBS environment variable if provided
    if args.subprocess_jobs:
        os.environ['PIPE_WORKER_SUBPROCESS_JOBS'] = args.subprocess_jobs

    # Set PIPE_WORKER_SCOPES environment variable if provided
    if args.scopes:
        os.environ['PIPE_WORKER_SCOPES'] = args.scopes

    # Set PostgreSQL environment variables if provided
    if args.postgres:
        os.environ['POSTGRES_HOST'], os.environ['POSTGRES_PORT'], os.environ['POSTGRES_USER'], os.environ['POSTGRES_PASSWORD'], os.environ['POSTGRES_DATABASE'] = args.postgres.split(':')

    # Run the worker
    asyncio.run(pete.worker.test_main(args.all))


def run_bucket(args):
    # Set environment variables for bucket
    if args.binding:
        os.environ['BUCKET_SERVER_HOST'], os.environ['BUCKET_SERVER_PORT'] = args.binding.split(':')

    # Run the bucket
    pete.bucket.main()

def run_demo():
    # Run the demo
    pete.examples.demo.main()


def run_example():
    # Run the example
    pete.examples.example.setup()


def upload_pipe_code(file_path, binding, lazy_steps):
    if binding:
        os.environ['PIPE_WORKER_HOST'], os.environ['PIPE_WORKER_PORT'] = binding.split(':')
    pete.hub.upload_pipe_code_from_file(file_path, lazy_steps)


def submit_pipe_code(file_path, binding, bucket_binding, scope):
    if binding:
        os.environ['PIPE_WORKER_HOST'], os.environ['PIPE_WORKER_PORT'] = binding.split(':')

    if bucket_binding:
        os.environ['BUCKET_CLIENT_HOST'], os.environ['BUCKET_CLIENT_PORT'] = bucket_binding.split(':')

    pete.hub.submit_pipe_code_from_file(file_path, scope)


def display_status(args):
    if args.binding:
        os.environ['PIPE_WORKER_HOST'], os.environ['PIPE_WORKER_PORT'] = args.binding.split(':')
    client = pete.hub.HubClient()
    refuse_count = 0
    def display_status_worker():
        nonlocal refuse_count
        try:
            data = client.get_step_count()
        except ConnectionRefusedError:
            print('Connection refused' + '.' * (refuse_count % 3))
            refuse_count += 1
            return 1
        except OSError as e:  # socket error
            print(f'{e}')
            return 1
        # client.get_step_count()
        # pete.hub.get_step_count(args.binding)
        for row in data:
            name, amount = row['status'], row['amount']
            print(f'{name}: {amount:,}')
        print(f'total: {sum([row["amount"] for row in data]):,}')
        return len(data) + 1
    if not args.subscribe:
        display_status_worker()
    else:
        last_length = 0

        while True:
            try:
                for _ in range(last_length):
                    delete_last_line()
                last_length = display_status_worker()
                time.sleep(3)
            except KeyboardInterrupt:
                print('\n - Have a great day! :)\n')
                break


def fetch_errors(args):
    if args.binding:
        os.environ['PIPE_WORKER_HOST'], os.environ['PIPE_WORKER_PORT'] = args.binding.split(':')

    try:
        count = int(args.count)
    except ValueError:
        count = 25

    exclude = args.exclude
    if not isinstance(exclude, str):
        exclude = None
    elif ',' in exclude:
        exclude = exclude.split(',')

    print('exclude', exclude)

    client = pete.hub.HubClient()
    return_value = client.fetch_errors(count, exclude)
    count, total, table = return_value['count'], return_value['total'], return_value['table']
    print(f'Fetched {count} errors of {total} total errors.\n')
    for row in table:
        _id, step, msg, _trace = row['id'], row['step'], row['msg'], row['trace']
        print(f'ID: \n  {_id}')
        print(f'Step: \n  {json.dumps(step, indent=4)}')
        print(f'Message: \n  {msg}')
        print(f'Trace: \n  {_trace}\n\n--**--\n')


def has_postgres_env_vars() -> bool:
    return all([var in os.environ for var in [
        'POSTGRES_HOST', 'POSTGRES_PORT', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DATABASE']])


def cli():
    parser = argparse.ArgumentParser(description='Buelon command-line interface')
    parser.add_argument('-v', '--version', action='version', version='Buelon 1.0.66-alpha26')
    parser.add_argument('-b', '--binding', help='Binding for uploading pipe code (host:port)')
    parser.add_argument('file_path', nargs='?', default='nothing', help='File path for uploading pipe code')

    subparsers = parser.add_subparsers(title='Commands', dest='command', required=False)

    # Check if environment variables are already set
    hub_binding_required = not ('PIPELINE_HOST' in os.environ and 'PIPELINE_PORT' in os.environ)
    hub_bucket_required = not ('BUCKET_CLIENT_HOST' in os.environ and 'BUCKET_CLIENT_PORT' in os.environ)
    if os.environ.get('USING_POSTGRES_BUCKET', 'false') == 'true':
        hub_bucket_required = not has_postgres_env_vars()

    worker_binding_required = not ('PIPE_WORKER_HOST' in os.environ and 'PIPE_WORKER_PORT' in os.environ)
    worker_bucket_required = not ('BUCKET_CLIENT_HOST' in os.environ and 'BUCKET_CLIENT_PORT' in os.environ)
    if os.environ.get('USING_POSTGRES_HUB', 'false') == 'true':
        worker_binding_required = not has_postgres_env_vars()
    if os.environ.get('USING_POSTGRES_BUCKET', 'false') == 'true':
        worker_bucket_required = not has_postgres_env_vars()

    bucket_binding_required = not ('BUCKET_SERVER_HOST' in os.environ and 'BUCKET_SERVER_PORT' in os.environ)

    # Pipe file run
    file_parser = subparsers.add_parser('upload', help='Upload pipe code from a file')
    file_parser.add_argument('-b', '--hub-binding', required=worker_binding_required, help='Binding to hub (host:port)')
    file_parser.add_argument('-f', '--file-path', help='File path for uploading pipe code', dest='file_path')
    file_parser.add_argument('-l', '--lazy', default=False, action=argparse.BooleanOptionalAction, dest='lazy')

    # Hub command
    hub_parser = subparsers.add_parser('hub', help='Run the hub')
    hub_parser.add_argument('-b', '--binding', required=hub_binding_required, help='Main binding for hub (host:port)')
    hub_parser.add_argument('-k', '--bucket-binding', required=hub_bucket_required, help='Bucket binding (host:port)')
    hub_parser.add_argument('-p', '--postgres', help='Postgres connection (host:port:user:password:database)')

    # Worker command
    worker_parser = subparsers.add_parser('worker', help='Run the worker')
    worker_parser.add_argument('-b', '--binding', required=worker_binding_required, help='Main binding for worker (host:port)')
    worker_parser.add_argument('-k', '--bucket-binding', required=worker_bucket_required, help='Bucket binding (host:port)')
    worker_parser.add_argument('-j', '--subprocess-jobs', choices=['true', 'false'], help='Set PIPE_WORKER_SUBPROCESS_JOBS environment variable')
    worker_parser.add_argument('-s', '--scopes', help='Set PIPE_WORKER_SCOPES environment variable')
    worker_parser.add_argument('-p', '--postgres', help='Postgres connection (host:port:user:password:database)')
    worker_parser.add_argument('-a', '--all', default=False, action=argparse.BooleanOptionalAction, help='Include all status')

    # Worker command
    test_parser = subparsers.add_parser('test', help='Run the Test worker')
    test_parser.add_argument('-b', '--binding', required=worker_binding_required, help='Main binding for worker (host:port)')
    test_parser.add_argument('-k', '--bucket-binding', required=worker_bucket_required, help='Bucket binding (host:port)')
    test_parser.add_argument('-j', '--subprocess-jobs', choices=['true', 'false'], help='Set PIPE_WORKER_SUBPROCESS_JOBS environment variable')
    test_parser.add_argument('-s', '--scopes', help='Set PIPE_WORKER_SCOPES environment variable')
    test_parser.add_argument('-p', '--postgres', help='Postgres connection (host:port:user:password:database)')
    test_parser.add_argument('-a', '--all', default=False, action=argparse.BooleanOptionalAction, help='Include all status')

    # Bucket command
    bucket_parser = subparsers.add_parser('bucket', help='Run the bucket')
    bucket_parser.add_argument('-b', '--binding', required=bucket_binding_required, help='Binding for bucket (host:port)')

    # Status
    status_parser = subparsers.add_parser('status', help='Check the status of the pipeline')
    status_parser.add_argument('-b', '--binding', required=worker_binding_required, help='Main binding for hub (host:port)')
    status_parser.add_argument('-s', '--subscribe', default=False, action=argparse.BooleanOptionalAction, help='Subscribe to status updates')

    # Reset Errors
    reset_parser = subparsers.add_parser('reset', help='Reset errors')
    reset_parser.add_argument('-b', '--binding', required=worker_binding_required, help='Main binding for hub (host:port)')
    reset_parser.add_argument('-w', '--include_working', default='false', choices=['true', 'false'], help='Whether to reset status \'working\'')

    # Delete steps
    delete_parser = subparsers.add_parser('delete', help='Delete steps')
    delete_parser.add_argument('-b', '--binding', required=worker_binding_required, help='Main binding for hub (host:port)')
    # delete_parser.add_argument('-s', '--step_id', help='Step ID to delete')

    # Fetch Errors
    error_fetch_parser = subparsers.add_parser('errors', help='View Error Logs')
    error_fetch_parser.add_argument('-b', '--binding', required=worker_binding_required,  help='Main binding for hub (host:port)')
    error_fetch_parser.add_argument('-c', '--count', default='10', help='Amount of error logs to view (must be int)')
    error_fetch_parser.add_argument('-e', '--exclude', default=None, help='Exclude a specific strings from error message. Commas exclude multiple messages')

    # Fetch Errors
    run_step_parser = subparsers.add_parser('run-step', help='View Error Logs')
    run_step_parser.add_argument('-s', '--step', required=True, help='The step id')

    # Fetch Errors
    submit_parser = subparsers.add_parser('submit', help='View Error Logs')
    submit_parser.add_argument('-f', '--file', required=True, help='File path to buelon script')
    submit_parser.add_argument('-k', '--bucket-binding', required=worker_bucket_required, help='Bucket binding (host:port)')
    submit_parser.add_argument('-b', '--binding', required=worker_binding_required, help='Main binding for hub (host:port)')
    submit_parser.add_argument('-s', '--scope', default=pete.worker.DEFAULT_SCOPES.split(',')[-1])

    # Repair
    repair_parser = subparsers.add_parser('repair', help='Reset errors')
    repair_parser.add_argument('-b', '--binding', required=worker_binding_required, help='Main binding for hub (host:port)')

    # Repair
    run_parser = subparsers.add_parser('run', help='Run script locally (Alpha Command)')
    run_parser.add_argument('-f', '--file', required=True, help='File path to buelon script')

    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run the demo')
    # demo_parser.set_defaults(func=run_demo)

    # Example command
    example_parser = subparsers.add_parser('example', help='Run the example')
    # example_parser.set_defaults(func=run_example)

    # Parse arguments
    args, remaining_args = parser.parse_known_args()
    # Handle the commands
    if args.command == 'hub':
        run_hub(args)
    elif args.command == 'worker':
        run_worker(args)
    elif args.command == 'test':
        run_test(args)
    elif args.command == 'bucket':
        run_bucket(args)
    elif args.command == 'demo':
        run_demo()
    elif args.command == 'example':
        run_example()
    elif args.command == 'upload':
        upload_pipe_code(args.file_path, args.hub_binding, args.lazy)
    elif args.command == 'submit':
        submit_pipe_code(args.file, args.binding, args.bucket_binding, args.scope)
    elif args.command == 'reset':
        if args.binding:
            os.environ['PIPE_WORKER_HOST'], os.environ['PIPE_WORKER_PORT'] = args.binding.split(':')
        # pete.hub.reset_errors(args.include_working is not None)
        client = pete.hub.HubClient()
        client.reset_errors(args.include_working == 'true')
    elif args.command == 'status':
        display_status(args)
    elif args.command == 'delete':
        if args.binding:
            os.environ['PIPE_WORKER_HOST'], os.environ['PIPE_WORKER_PORT'] = args.binding.split(':')
        client = pete.hub.HubClient()
        client.sync_delete_steps()
    elif args.command == 'errors':
        fetch_errors(args)
    elif args.command == 'repair':
        if args.binding:
            os.environ['PIPE_WORKER_HOST'], os.environ['PIPE_WORKER_PORT'] = args.binding.split(':')
        client = pete.hub.HubClient()
        client.repair()
    elif args.command == 'run-step':
        if args.binding:
            os.environ['PIPE_WORKER_HOST'], os.environ['PIPE_WORKER_PORT'] = args.binding.split(':')
        if not os.environ.get('PIPE_WORKER_HOST') or not os.environ.get('PIPE_WORKER_PORT'):
            raise ValueError('Binding is required when running a step. Set env vars `PIPE_WORKER_HOST` and `PIPE_WORKER_PORT`')

        step_id = args.step

        logging.getLogger().setLevel(logging.DEBUG)
        pete.worker.job(step_id)
    elif args.command == 'run':
        if args.file:
            with open(args.file) as f:
                pete.core.pipe_interpreter.run_code(f.read())
    else:
        # Handle the case where a file path is given without a command
        if args.binding and remaining_args:
            file_path = remaining_args[0]
            file_path.close()
            # upload_pipe_code(file_path, args.binding)
        elif remaining_args:
            parser.error('Binding is required when uploading pipe code from file. Use -b or --binding.')
        else:
            parser.print_help()
            sys.exit(1)


if __name__ == '__main__':
    cli()



# import argparse
# import os
# import sys
#
# # Import necessary modules from buelon
# import buelon as pete
#
# def run_hub(args):
#     # Set environment variables for hub
#     os.environ['PIPELINE_HOST'], os.environ['PIPELINE_PORT'] = args.main_binding.split(':')
#     os.environ['BUCKET_CLIENT_HOST'], os.environ['BUCKET_CLIENT_PORT'] = args.bucket_binding.split(':')
#
#     # Set PostgreSQL environment variables if provided
#     if args.postgres:
#         os.environ['POSTGRES_HOST'], os.environ['POSTGRES_PORT'], os.environ['POSTGRES_USER'], os.environ['POSTGRES_PASSWORD'], os.environ['POSTGRES_DATABASE'] = args.postgres.split(':')
#
#     # Run the hub
#     pete.hub.main()
#
# def run_worker(args):
#     # Set environment variables for worker
#     os.environ['PIPE_WORKER_HOST'], os.environ['PIPE_WORKER_PORT'] = args.main_binding.split(':')
#     os.environ['BUCKET_CLIENT_HOST'], os.environ['BUCKET_CLIENT_PORT'] = args.bucket_binding.split(':')
#
#     # Set PIPE_WORKER_SUBPROCESS_JOBS environment variable if provided
#     if args.subprocess_jobs:
#         os.environ['PIPE_WORKER_SUBPROCESS_JOBS'] = args.subprocess_jobs
#
#     # Set PIPE_WORKER_SCOPES environment variable if provided
#     if args.scopes:
#         os.environ['PIPE_WORKER_SCOPES'] = args.scopes
#
#     # Set PostgreSQL environment variables if provided
#     if args.postgres:
#         os.environ['POSTGRES_HOST'], os.environ['POSTGRES_PORT'], os.environ['POSTGRES_USER'], os.environ['POSTGRES_PASSWORD'], os.environ['POSTGRES_DATABASE'] = args.postgres.split(':')
#
#     # Run the worker
#     pete.worker.main()
#
# def run_bucket(args):
#     # Set environment variables for bucket
#     os.environ['BUCKET_SERVER_HOST'], os.environ['BUCKET_SERVER_PORT'] = args.binding.split(':')
#
#     # Run the bucket
#     pete.bucket.main()
#
# def run_demo():
#     # Run the demo
#     pete.examples.demo.main()
#
# def run_example():
#     # Run the example
#     pete.examples.example.main()
#
# def upload_pipe_code(file_path, binding):
#     os.environ['PIPE_WORKER_HOST'], os.environ['PIPE_WORKER_PORT'] = binding.split(':')
#     pete.hub.upload_pipe_code_from_file(file_path)
#
# def cli():
#     parser = argparse.ArgumentParser(description='Buelon command-line interface')
#     parser.add_argument('-v', '--version', action='version', version='Buelon 1.0.0')
#     subparsers = parser.add_subparsers(title='Commands', dest='command')
#
#     # Check if environment variables are already set
#     hub_binding_required = not ('PIPELINE_HOST' in os.environ and 'PIPELINE_PORT' in os.environ)
#     hub_bucket_required = not ('BUCKET_CLIENT_HOST' in os.environ and 'BUCKET_CLIENT_PORT' in os.environ)
#
#     worker_binding_required = not ('PIPE_WORKER_HOST' in os.environ and 'PIPE_WORKER_PORT' in os.environ)
#     worker_bucket_required = not ('BUCKET_CLIENT_HOST' in os.environ and 'BUCKET_CLIENT_PORT' in os.environ)
#
#     bucket_binding_required = not ('BUCKET_SERVER_HOST' in os.environ and 'BUCKET_SERVER_PORT' in os.environ)
#
#     # Hub command
#     hub_parser = subparsers.add_parser('hub', help='Run the hub')
#     hub_parser.add_argument('-b', '--main-binding', required=hub_binding_required, help='Main binding for hub (host:port)')
#     hub_parser.add_argument('-k', '--bucket-binding', required=hub_bucket_required, help='Bucket binding (host:port)')
#     hub_parser.add_argument('-p', '--postgres', help='Postgres connection (host:port:user:password:database)')
#
#     # Worker command
#     worker_parser = subparsers.add_parser('worker', help='Run the worker')
#     worker_parser.add_argument('-b', '--main-binding', required=worker_binding_required, help='Main binding for worker (host:port)')
#     worker_parser.add_argument('-k', '--bucket-binding', required=worker_bucket_required, help='Bucket binding (host:port)')
#     worker_parser.add_argument('-s', '--subprocess-jobs', choices=['true', 'false'], help='Set PIPE_WORKER_SUBPROCESS_JOBS environment variable')
#     worker_parser.add_argument('--scopes', help='Set PIPE_WORKER_SCOPES environment variable')
#     worker_parser.add_argument('-p', '--postgres', help='Postgres connection (host:port:user:password:database)')
#
#     # Bucket command
#     bucket_parser = subparsers.add_parser('bucket', help='Run the bucket')
#     bucket_parser.add_argument('-b', '--binding', required=bucket_binding_required, help='Binding for bucket (host:port)')
#
#     # Demo command
#     demo_parser = subparsers.add_parser('demo', help='Run the demo')
#     demo_parser.set_defaults(func=run_demo)
#
#     # Example command
#     example_parser = subparsers.add_parser('example', help='Run the example')
#     example_parser.set_defaults(func=run_example)
#
#     # Parse arguments
#     args, remaining_args = parser.parse_known_args()
#
#     # Handle the commands
#     if args.command == 'hub':
#         run_hub(args)
#     elif args.command == 'worker':
#         run_worker(args)
#     elif args.command == 'bucket':
#         run_bucket(args)
#     elif args.command == 'demo':
#         run_demo()
#     elif args.command == 'example':
#         run_example()
#     else:
#         # Handle the case where a file path is given without a command
#         if remaining_args:
#             file_path = remaining_args[-1]
#             if '--binding' in remaining_args or '-b' in remaining_args:
#                 index = remaining_args.index('--binding') + 1 if '--binding' in remaining_args else remaining_args.index('-b') + 1
#                 binding = remaining_args[index]
#                 upload_pipe_code(file_path, binding)
#             else:
#                 parser.error('Binding is required when uploading pipe code from file.')
#         else:
#             parser.print_help()
#             sys.exit(1)
#
# if __name__ == '__main__':
#     cli()
#
