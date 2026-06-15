## Next Claude Code session — June 28

### Context
Phase 1 complete. Pipeline operational. Waiting for EMIS 2-week signal run to select vertical.

### Session start commands
**WSL**
```bash
cd /mnt/d/Projects/cpds-ai
git pull origin main
git log --oneline -5
cat config/vertical.yml
ls /mnt/d/Projects/emis-exports/digest/
~/venvs/ai-research/bin/python scripts/self_improve.py phase_transition
```

### What to do
1. Read the EMIS digest file in `/mnt/d/Projects/emis-exports/digest/`
2. Show Claude.ai (architect) the signal summary and recommend a vertical
3. Once Claude.ai confirms the vertical selection:
   - Update `config/vertical.yml` — set `status: active`, populate all keyword/topic fields from the candidate config already in the file
   - Update `config/sources.yml` — enable `product_hunt: enabled: true` if token is in `.env`
   - Update `curate.py` prompts — replace generic "automation and AI tools" framing with vertical-specific language
4. Run `source_runner.py` with live vertical config
5. Run `curate.py` — review first real draft output
6. Flag any prompt quality issues to Claude.ai for revision
7. Write session audit, commit, push

### Pending user actions to check on session start
- [ ] Task Scheduler tasks registered? (`schtasks /Query /TN "CPDS-AI" /FO LIST`)
- [ ] Beehiiv Scale plan active? (Max trial expires ~June 28)
- [ ] Product Hunt API token in `.env`?
- [ ] Welcome email automations configured in Beehiiv?
