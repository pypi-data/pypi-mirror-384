import os
import subprocess
import sys
import time
import traceback

from alarmistic.teams import send_message_to_webhook, webhooks
from functions.calculate_execution_time import calculate_execution_time
from logger.logger_config import setup_logger
from runner_configs import process_folders, test_folders

logger = setup_logger()


def validate_data_contracts(path, errors):
    logger.info('Running data contract tests in: %s', path)
    result = subprocess.run(['pytest', '-v'], cwd=path)
    if result.returncode != 0:
        msg = f'❌ Data contract tests failed in: {path}'
        logger.error(msg)
        errors.append(msg)
    else:
        logger.info('Data contract tests passed in: %s', path)


def execute_process(script_path, errors):
    logger.info('Running process script: %s', script_path)
    result = subprocess.run(['python', script_path], cwd='.')
    if result.returncode != 0:
        msg = f'❌ Main process failed for script: {script_path}'
        logger.error(msg)
        errors.append(msg)
    else:
        logger.info('Process completed successfully for: %s', script_path)


@calculate_execution_time
def main():
    errors = []

    ##################################################
    # Validate sources
    ##################################################
    validate_data_contracts(path='contracts/sources', errors=errors)

    ##################################################
    # Run main process
    ##################################################
    for folder in process_folders:
        try:
            execute_process(script_path=folder, errors=errors)
        except Exception:
            error_trace = traceback.format_exc()
            logger.error('Unexpected error:\n%s', error_trace)
            errors.append(f'❌ Unexpected error in {folder}:\n``````')

    ###################################################
    # Refresh Metadata
    ###################################################
    execute_process(
        script_path='refresh_metadata/refresh_metadata.py', errors=errors
    )

    ##################################################
    # Validate data after data process
    ##################################################
    for folder in test_folders:
        try:
            validate_data_contracts(path=folder, errors=errors)
        except Exception:
            error_trace = traceback.format_exc()
            logger.error('Unexpected error:\n%s', error_trace)
            errors.append(f'❌ Unexpected error in {folder}:\n``````')

    ##################################################
    # Final Alarmistic message
    ##################################################
    if errors:
        full_message = '\n'.join(errors)
        logger.error('Process completed with errors:\n%s', full_message)

        for (
            config
        ) in webhooks.values():  # Itera sobre os webhooks configurados
            send_message_to_webhook(
                webhook_url=config['url'],
                target=config['target'],
                message_text=f'❌ pygalp process completed with errors:\n{full_message}',
            )
    else:
        logger.info('Process completed successfully.')
        for config in webhooks.values():
            send_message_to_webhook(
                webhook_url=config['url'],
                target=config['target'],
                message_text='✅ pygalp process completed successfully',
            )


if __name__ == '__main__':
    main()
