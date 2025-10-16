# Workstack shell integration for bash
# This function wraps the workstack CLI to provide seamless worktree switching

workstack() {
  # Don't intercept if we're doing shell completion
  [ -n "$_WORKSTACK_COMPLETE" ] && { command workstack "$@"; return; }

  local script_path exit_status
  script_path=$(WORKSTACK_SHELL=bash command workstack __shell "$@")
  exit_status=$?

  # Passthrough mode: run the original command directly
  [ "$script_path" = "__WORKSTACK_PASSTHROUGH__" ] && { command workstack "$@"; return; }

  # If __shell returned non-zero, error messages are already sent to stderr
  [ $exit_status -ne 0 ] && return $exit_status

  # Source the script file if it exists
  if [ -n "$script_path" ] && [ -f "$script_path" ]; then
    source "$script_path"
    local source_exit=$?

    # Clean up unless WORKSTACK_KEEP_SCRIPTS is set
    if [ -z "$WORKSTACK_KEEP_SCRIPTS" ]; then
      rm -f "$script_path"
    fi

    return $source_exit
  fi
}
