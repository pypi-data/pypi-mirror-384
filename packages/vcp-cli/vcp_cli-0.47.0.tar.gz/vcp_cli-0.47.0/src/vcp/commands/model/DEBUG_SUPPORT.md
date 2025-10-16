# VCP Model Commands

## Reporting Issues

If you encounter issues with VCP model commands, please include debug output in your support ticket:

### For Authentication Issues
```bash
vcp model init --model-name test-issue --model-version v1 --license-type MIT --work-dir /tmp/test-issue --verbose --debug --debug-file /tmp/vcp-debug.log
```

### For General Issues
```bash
vcp model <command> --verbose --debug --debug-file /tmp/vcp-debug.log
```

### Share Debug Output
1. Run the command above
2. Copy the contents of `/tmp/vcp-debug.log`
3. Paste in your support ticket

**Note**: Debug files automatically mask sensitive information (tokens, URLs, emails) and are safe to share.

## Available Commands

- `vcp model init` - Initialize a new model
- `vcp model list` - List available models
- `vcp model download` - Download model files
- `vcp model submit` - Submit model for review
- `vcp model stage` - Stage model files
- `vcp model status` - Check submission status
- `vcp model assist` - Get model submission guidance

## Getting Help

- Use `vcp model <command> --help` for command-specific help
- Use `--verbose` for detailed output
- Use `--debug` for troubleshooting (includes sensitive info)
- Use `--debug-file` to save safe debug output for support tickets
