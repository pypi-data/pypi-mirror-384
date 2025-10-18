#!/usr/bin/env bash
set -euo pipefail

# create-release-packages.sh (workflow-local)
# Build Spec Kit template release archives for each supported AI assistant and script type.
# Usage: .github/workflows/scripts/create-release-packages.sh <version>
#   Version argument should include leading 'v'.
#   Optionally set AGENTS and/or SCRIPTS env vars to limit what gets built.
#     AGENTS  : space or comma separated subset of: claude gemini copilot cursor-agent qwen opencode windsurf codex (default: all)
#     SCRIPTS : space or comma separated subset of: sh ps (default: both)
#   Examples:
#     AGENTS=claude SCRIPTS=sh $0 v0.2.0
#     AGENTS="copilot,gemini" $0 v0.2.0
#     SCRIPTS=ps $0 v0.2.0

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version-with-v-prefix>" >&2
  exit 1
fi
NEW_VERSION="$1"
if [[ ! $NEW_VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Version must look like v0.0.0" >&2
  exit 1
fi

echo "Building release packages for $NEW_VERSION"

# Create and use .genreleases directory for all build artifacts
GENRELEASES_DIR=".genreleases"
mkdir -p "$GENRELEASES_DIR"
rm -rf "$GENRELEASES_DIR"/* || true

rewrite_paths() {
  sed -E \
    -e 's@(/?)memory/@.specify/memory/@g' \
    -e 's@(/?)scripts/@.specify/scripts/@g' \
    -e 's@(/?)templates/@.specify/templates/@g'
}

generate_commands() {
  local agent=$1 ext=$2 arg_format=$3 output_dir=$4 script_variant=$5
  mkdir -p "$output_dir"
  
  # Load command-rules.md for prepending (universal pre-execution rules)
  local command_rules_content=""
  if [[ -f "memory/command-rules.md" ]]; then
    command_rules_content=$(tr -d '\r' < "memory/command-rules.md")
    echo "Loaded command-rules.md for universal pre-execution injection"
  else
    echo "Warning: memory/command-rules.md not found - commands will not have implicit behavior support" >&2
  fi
  
  for template in templates/commands/*.md; do
    [[ -f "$template" ]] || continue
    local name description script_command agent_script_command body
    name=$(basename "$template" .md)
    
    # Normalize line endings
    file_content=$(tr -d '\r' < "$template")
    
    # Extract description and script command from YAML frontmatter
    description=$(printf '%s\n' "$file_content" | awk '/^description:/ {sub(/^description:[[:space:]]*/, ""); print; exit}')
    script_command=$(printf '%s\n' "$file_content" | awk -v sv="$script_variant" '/^[[:space:]]*'"$script_variant"':[[:space:]]*/ {sub(/^[[:space:]]*'"$script_variant"':[[:space:]]*/, ""); print; exit}')
    
    if [[ -z $script_command ]]; then
      echo "Warning: no script command found for $script_variant in $template" >&2
      script_command="(Missing script command for $script_variant)"
    fi
    
    # Extract agent_script command from YAML frontmatter if present
    agent_script_command=$(printf '%s\n' "$file_content" | awk '
      /^agent_scripts:$/ { in_agent_scripts=1; next }
      in_agent_scripts && /^[[:space:]]*'"$script_variant"':[[:space:]]*/ {
        sub(/^[[:space:]]*'"$script_variant"':[[:space:]]*/, "")
        print
        exit
      }
      in_agent_scripts && /^[a-zA-Z]/ { in_agent_scripts=0 }
    ')
    
    # Replace {SCRIPT} placeholder with the script command
    body=$(printf '%s\n' "$file_content" | sed "s|{SCRIPT}|${script_command}|g")
    
    # Replace {AGENT_SCRIPT} placeholder with the agent script command if found
    if [[ -n $agent_script_command ]]; then
      body=$(printf '%s\n' "$body" | sed "s|{AGENT_SCRIPT}|${agent_script_command}|g")
    fi
    
    # Remove the scripts: and agent_scripts: sections from frontmatter while preserving YAML structure
    body=$(printf '%s\n' "$body" | awk '
      /^---$/ { print; if (++dash_count == 1) in_frontmatter=1; else in_frontmatter=0; next }
      in_frontmatter && /^scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^agent_scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^[a-zA-Z].*:/ && skip_scripts { skip_scripts=0 }
      in_frontmatter && skip_scripts && /^[[:space:]]/ { next }
      { print }
    ')
    
    # Apply other substitutions
    body=$(printf '%s\n' "$body" | sed "s/{ARGS}/$arg_format/g" | sed "s/__AGENT__/$agent/g" | rewrite_paths)
    
    # Append command-rules.md content at the end (simpler, no frontmatter extraction needed)
    if [[ -n $command_rules_content ]]; then
      body=$(printf '%s\n\n---\n\n%s' "$body" "$command_rules_content")
    fi
    
    case $ext in
      toml)
        body=$(printf '%s\n' "$body" | sed 's/\\/\\\\/g')
        { echo "description = \"$description\""; echo; echo "prompt = \"\"\""; echo "$body"; echo "\"\"\""; } > "$output_dir/sp.$name.$ext" ;;
      md)
        echo "$body" > "$output_dir/sp.$name.$ext" ;;
      prompt.md)
        echo "$body" > "$output_dir/sp.$name.$ext" ;;
    esac
  done
}

build_variant() {
  local agent=$1 script=$2
  local base_dir="$GENRELEASES_DIR/sdd-${agent}-package-${script}"
  echo "Building $agent ($script) package..."
  mkdir -p "$base_dir"
  
  # Copy base structure but filter scripts by variant
  SPEC_DIR="$base_dir/.specify"
  mkdir -p "$SPEC_DIR"
  
  [[ -d memory ]] && { cp -r memory "$SPEC_DIR/"; echo "Copied memory -> .specify"; }
  
  # Copy AGENTS.md from protocol-templates to project root (not in .specify/memory)
  if [[ -f protocol-templates/AGENTS.md ]]; then
    cp protocol-templates/AGENTS.md "$base_dir/AGENTS.md"
    echo "Copied AGENTS.md to project root (from protocol-templates)"
  fi
  # If constitutionplus.md exists, overwrite constitution.md in release package
  if [[ -f memory/constitutionplus.md ]]; then
    mkdir -p "$SPEC_DIR/memory"
    cp memory/constitutionplus.md "$SPEC_DIR/memory/constitution.md"
    echo "Injected constitutionplus.md as .specify/memory/constitution.md"
    # Do not ship constitutionplus.md in the archive
    rm -f "$SPEC_DIR/memory/constitutionplus.md" 2>/dev/null || true
  fi
  
  # Only copy the relevant script variant directory
  if [[ -d scripts ]]; then
    mkdir -p "$SPEC_DIR/scripts"
    case $script in
      sh)
        [[ -d scripts/bash ]] && { cp -r scripts/bash "$SPEC_DIR/scripts/"; echo "Copied scripts/bash -> .specify/scripts"; }
        # Copy any script files that aren't in variant-specific directories
        find scripts -maxdepth 1 -type f -exec cp {} "$SPEC_DIR/scripts/" \; 2>/dev/null || true
        ;;
      ps)
        [[ -d scripts/powershell ]] && { cp -r scripts/powershell "$SPEC_DIR/scripts/"; echo "Copied scripts/powershell -> .specify/scripts"; }
        # Copy any script files that aren't in variant-specific directories
        find scripts -maxdepth 1 -type f -exec cp {} "$SPEC_DIR/scripts/" \; 2>/dev/null || true
        ;;
    esac
  fi
  
  [[ -d templates ]] && { mkdir -p "$SPEC_DIR/templates"; find templates -type f -not -path "templates/commands/*" -not -name "vscode-settings.json" -exec cp --parents {} "$SPEC_DIR"/ \; ; echo "Copied templates -> .specify/templates"; }
  
  # NOTE: We substitute {ARGS} internally. Outward tokens differ intentionally:
  #   * Markdown/prompt (claude, copilot, cursor-agent, opencode): $ARGUMENTS
  #   * TOML (gemini, qwen): {{args}}
  # This keeps formats readable without extra abstraction.

  # Generate agent-specific rule file
  generate_agent_rules() {
    local agent=$1
    local base_dir=$2
    
    # Load the base AGENTS.md content
    local agents_content=""
    if [[ -f "protocol-templates/AGENTS.md" ]]; then
      agents_content=$(tr -d '\r' < "protocol-templates/AGENTS.md")
    else
      echo "Warning: protocol-templates/AGENTS.md not found - cannot generate agent rules" >&2
      return 1
    fi
    
    # Create agent-specific preface
    local agent_name=""
    case $agent in
      claude) agent_name="Claude Code" ;;
      gemini) agent_name="Gemini CLI" ;;
      copilot) agent_name="GitHub Copilot" ;;
      cursor-agent) agent_name="Cursor" ;;
      qwen) agent_name="Qwen Code" ;;
      opencode) agent_name="opencode" ;;
      windsurf) agent_name="Windsurf" ;;
      codex) agent_name="Codex CLI" ;;
      kilocode) agent_name="Kilo Code" ;;
      auggie) agent_name="Auggie CLI" ;;
      roo) agent_name="Roo Code" ;;
      codebuddy) agent_name="CodeBuddy" ;;
      q) agent_name="Amazon Q Developer CLI" ;;
      *) agent_name="$agent" ;;
    esac
    
    local preface="# $agent_name Rules

This file is generated during init for the selected agent.

"
    
    # Generate the complete content
    local full_content="${preface}${agents_content}"
    
    # Write to appropriate location based on agent
    case $agent in
      cursor-agent)
        mkdir -p "$base_dir/.cursor/rules"
        echo "$full_content" > "$base_dir/.cursor/rules/guidelines.md"
        echo "Generated .cursor/rules/guidelines.md"
        ;;
      gemini)
        echo "$full_content" > "$base_dir/GEMINI.md"
        echo "Generated GEMINI.md"
        ;;
      qwen)
        echo "$full_content" > "$base_dir/QWEN.md"
        echo "Generated QWEN.md"
        ;;
      claude)
        echo "$full_content" > "$base_dir/CLAUDE.md"
        echo "Generated CLAUDE.md"
        ;;
      auggie)
        echo "$full_content" > "$base_dir/AUGGIE.md"
        echo "Generated AUGGIE.md"
        ;;
      q)
        echo "$full_content" > "$base_dir/Q.md"
        echo "Generated Q.md"
        ;;
      opencode)
        echo "$full_content" > "$base_dir/opencode.md"
        echo "Generated opencode.md"
        ;;
      windsurf)
        echo "$full_content" > "$base_dir/windsurf.md"
        echo "Generated windsurf.md"
        ;;
      kilocode)
        echo "$full_content" > "$base_dir/kilocode.md"
        echo "Generated kilocode.md"
        ;;
      roo)
        echo "$full_content" > "$base_dir/roo.md"
        echo "Generated roo.md"
        ;;
      copilot)
        mkdir -p "$base_dir/.github"
        echo "$full_content" > "$base_dir/.github/copilot-instructions.md"
        echo "Generated .github/copilot-instructions.md"
        ;;
      codex)
        mkdir -p "$base_dir/.codex/rules"
        echo "$full_content" > "$base_dir/.codex/rules/guidelines.md"
        echo "Generated .codex/rules/guidelines.md"
        ;;
      codebuddy)
        mkdir -p "$base_dir/.codebuddy/rules"
        echo "$full_content" > "$base_dir/.codebuddy/rules/guidelines.md"
        echo "Generated .codebuddy/rules/guidelines.md"
        ;;
    esac
  }

  case $agent in
    claude)
      mkdir -p "$base_dir/.claude/commands"
      generate_commands claude md "\$ARGUMENTS" "$base_dir/.claude/commands" "$script"
      generate_agent_rules claude "$base_dir" ;;
    gemini)
      mkdir -p "$base_dir/.gemini/commands"
      generate_commands gemini toml "{{args}}" "$base_dir/.gemini/commands" "$script"
      generate_agent_rules gemini "$base_dir" ;;
    copilot)
      mkdir -p "$base_dir/.github/prompts"
      generate_commands copilot prompt.md "\$ARGUMENTS" "$base_dir/.github/prompts" "$script"
      # Create VS Code workspace settings
      mkdir -p "$base_dir/.vscode"
      [[ -f templates/vscode-settings.json ]] && cp templates/vscode-settings.json "$base_dir/.vscode/settings.json"
      generate_agent_rules copilot "$base_dir" ;;
    cursor-agent)
      mkdir -p "$base_dir/.cursor/commands"
      generate_commands cursor-agent md "\$ARGUMENTS" "$base_dir/.cursor/commands" "$script"
      generate_agent_rules cursor-agent "$base_dir" ;;
    qwen)
      mkdir -p "$base_dir/.qwen/commands"
      generate_commands qwen toml "{{args}}" "$base_dir/.qwen/commands" "$script"
      generate_agent_rules qwen "$base_dir" ;;
    opencode)
      mkdir -p "$base_dir/.opencode/command"
      generate_commands opencode md "\$ARGUMENTS" "$base_dir/.opencode/command" "$script"
      generate_agent_rules opencode "$base_dir" ;;
    windsurf)
      mkdir -p "$base_dir/.windsurf/workflows"
      generate_commands windsurf md "\$ARGUMENTS" "$base_dir/.windsurf/workflows" "$script"
      generate_agent_rules windsurf "$base_dir" ;;
    codex)
      mkdir -p "$base_dir/.codex/prompts"
      generate_commands codex md "\$ARGUMENTS" "$base_dir/.codex/prompts" "$script"
      generate_agent_rules codex "$base_dir" ;;
    kilocode)
      mkdir -p "$base_dir/.kilocode/workflows"
      generate_commands kilocode md "\$ARGUMENTS" "$base_dir/.kilocode/workflows" "$script"
      generate_agent_rules kilocode "$base_dir" ;;
    auggie)
      mkdir -p "$base_dir/.augment/commands"
      generate_commands auggie md "\$ARGUMENTS" "$base_dir/.augment/commands" "$script"
      generate_agent_rules auggie "$base_dir" ;;
    roo)
      mkdir -p "$base_dir/.roo/commands"
      generate_commands roo md "\$ARGUMENTS" "$base_dir/.roo/commands" "$script"
      generate_agent_rules roo "$base_dir" ;;
    codebuddy)
      mkdir -p "$base_dir/.codebuddy/commands"
      generate_commands codebuddy md "\$ARGUMENTS" "$base_dir/.codebuddy/commands" "$script"
      generate_agent_rules codebuddy "$base_dir" ;;

    q)
      mkdir -p "$base_dir/.amazonq/prompts"
      generate_commands q md "\$ARGUMENTS" "$base_dir/.amazonq/prompts" "$script"
      generate_agent_rules q "$base_dir" ;;
  esac
  ( cd "$base_dir" && zip -r "../spec-kit-template-${agent}-${script}-${NEW_VERSION}.zip" . )
  echo "Created $GENRELEASES_DIR/spec-kit-template-${agent}-${script}-${NEW_VERSION}.zip"
}

# Determine agent list
ALL_AGENTS=(claude gemini copilot cursor-agent qwen opencode windsurf codex kilocode auggie roo codebuddy q)
ALL_SCRIPTS=(sh ps)

norm_list() {
  # convert comma+space separated -> space separated unique while preserving order of first occurrence
  tr ',\n' '  ' | awk '{for(i=1;i<=NF;i++){if(!seen[$i]++){printf((out?" ":"") $i)}}}END{printf("\n")}'
}

validate_subset() {
  local type=$1; shift; local -n allowed=$1; shift; local items=("$@")
  local ok=1
  for it in "${items[@]}"; do
    local found=0
    for a in "${allowed[@]}"; do [[ $it == "$a" ]] && { found=1; break; }; done
    if [[ $found -eq 0 ]]; then
      echo "Error: unknown $type '$it' (allowed: ${allowed[*]})" >&2
      ok=0
    fi
  done
  return $ok
}

if [[ -n ${AGENTS:-} ]]; then
  mapfile -t AGENT_LIST < <(printf '%s' "$AGENTS" | norm_list)
  validate_subset agent ALL_AGENTS "${AGENT_LIST[@]}" || exit 1
else
  AGENT_LIST=("${ALL_AGENTS[@]}")
fi

if [[ -n ${SCRIPTS:-} ]]; then
  mapfile -t SCRIPT_LIST < <(printf '%s' "$SCRIPTS" | norm_list)
  validate_subset script ALL_SCRIPTS "${SCRIPT_LIST[@]}" || exit 1
else
  SCRIPT_LIST=("${ALL_SCRIPTS[@]}")
fi

echo "Agents: ${AGENT_LIST[*]}"
echo "Scripts: ${SCRIPT_LIST[*]}"

for agent in "${AGENT_LIST[@]}"; do
  for script in "${SCRIPT_LIST[@]}"; do
    build_variant "$agent" "$script"
  done
done

echo "Archives in $GENRELEASES_DIR:"
ls -1 "$GENRELEASES_DIR"/spec-kit-template-*-"${NEW_VERSION}".zip

