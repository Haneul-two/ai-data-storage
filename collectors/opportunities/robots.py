"""robots.txt 해석(와일드카드, `$`, 최장 일치, UA 그룹 선택). 표준 라이브러리 파서는 와일드카드를 지원하지 않는다."""
import re


def _pattern(path):
    anchored = path.endswith("$")
    body = re.escape(path[:-1] if anchored else path).replace(r"\*", ".*")
    return re.compile("^" + body + ("$" if anchored else ""))


class RobotsRules:
    def __init__(self, text):
        self.groups = []  # (agents, [(allow, path)])
        agents, rules, in_rules = [], [], False
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            field, value = (p.strip() for p in line.split(":", 1))
            field = field.lower()
            if field == "user-agent":
                if in_rules:
                    self.groups.append((agents, rules))
                    agents, rules, in_rules = [], [], False
                agents.append(value.lower())
            elif field in ("allow", "disallow"):
                in_rules = True
                if value:
                    rules.append((field == "allow", value))
        if agents:
            self.groups.append((agents, rules))

    def _select(self, user_agent):
        ua = user_agent.lower()
        best, best_len = None, -1
        for agents, rules in self.groups:
            for agent in agents:
                if agent != "*" and agent in ua and len(agent) > best_len:
                    best, best_len = rules, len(agent)
        if best is not None:
            return best
        merged = []
        for agents, rules in self.groups:
            if "*" in agents:
                merged.extend(rules)
        return merged

    def allowed(self, user_agent, path):
        verdict, length = True, -1
        for allow, pattern in self._select(user_agent):
            if _pattern(pattern).match(path) and (len(pattern) > length or (len(pattern) == length and allow)):
                verdict, length = allow, len(pattern)
        return verdict
