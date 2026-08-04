from app.dto.models import (
    AffixDTO,
    ItemDTO,
    IdolDTO,
    SkillDTO,
    BuildSummary,
    BuildDetails,
    BuildStatDTO,
    FilterRuleDTO,
)


def test_item_and_affix_instantiation():
    aff = AffixDTO(name="Frost Claw Level", tier=2)
    item = ItemDTO(name="Solarum Bracers", item_type="Gloves", slot="Hands", rarity="Exalted", is_exalted=True, affixes=[aff])
    assert item.name == "Solarum Bracers"
    assert item.affixes[0].name == "Frost Claw Level"


def test_idol_and_skill_and_buildsummary():
    idol = IdolDTO(name="Large Arcane Idol", size="Large", modifiers=["Chance to cast Flame Wave"])
    skill = SkillDTO(name="Frost Claw", description="A skill", level=20)
    summary = BuildSummary(name="Frost Claw Runemaster", tier="S", class_name="Mage", mastery="Runemaster", url="https://example")
    assert idol.size == "Large"
    assert skill.level == 20
    assert summary.tier == "S"


def test_builddetails_and_stats_and_filterrule():
    stat = BuildStatDTO(stat_name="Intelligence", value= "+100", priority=10)
    details = BuildDetails(name="Test Build", class_name="Mage", mastery="Runemaster", stats=[stat])
    rule = FilterRuleDTO(rule_type="SHOW", item_type="Helmet", rarity="Exalted", affixes=["Intelligence"], priority=100)
    assert details.stats[0].stat_name == "Intelligence"
    assert rule.priority == 100
