from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    timeout_brief = "Dočasně zakáže uživateli interakce na serveru."
    list_brief = "Vypíše uživatele se zatlumením."
    remove_brief = "Předčasně odebere umlčení uživateli."
    get_user_brief = "Vypíše informace o trestech uživatele"
    self_timeout_brief = "Dočasně si zakážeš interakce na serveru"
    reason_param = "Důvod umlčení uživatele."
    user_param = "Použij tag uživatele/uživatelů"
    remove_logs_param = "Odstraní záznam z databáze."
    missing_permission = "Na umlčení **{user_list}** nemám práva."
    timeout_field_text = "**Kdo:** {member}\n**Od:** {author}\n**Délka:** {starttime} - {endtime} ({length})\n**Navrácení:** {timestamp}\n**Důvod:** {reason}\n"
    list_none = "Nenalezeny žádné umlčení."
    timeout_too_short = "Délka umlčení je příliš krátká. Musí být alespoň 30s."
    past_time = "Nelze nastavit umlčení v minulosti."
    timeout_member_not_found = "{author} `{members}` jsem na serveru nenašel. Ujisti se, že jsi uživatele zadal správně pomocí @tag | name | ID."
    remove_reason = "{member}\nPředčasně odebráno"
    get_user_no_timeouts = "Uživatel nemá žádné tresty"
    manual_timeout = "Bez udání důvodu. (Discord GUI)"
    manual_remove = "{member}\nPředčasně odebráno (Discord GUI)"
    self_timeout_reason = "Sebeumlčení"
    self_timeout_success = "Sebeumlčení proběhlo úspěšně"