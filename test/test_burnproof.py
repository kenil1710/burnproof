"""Offline suite for BurnProof and BurnGate.

    cd test && python3 -m unittest -q test_burnproof test_attacks
"""
import ast
import json
import unittest
from pathlib import Path

import fixtures as F
import stub
import world
from fixtures import BP, TOKEN, TOKEN9, FILER, FILER2, FILER3, PROJECT, SITE, SNAP, TS, BLOCK, NOW, T

ROOT = Path(__file__).resolve().parent.parent
QUOTE = "burned 40% of the total supply"
PAGE = "Since launch our team has burned 40% of the total supply to a dead wallet."


class Base(unittest.TestCase):
    def setUp(self):
        self.w, self.bp, self.gate = F.deploy()
        F.page(PAGE)
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(410), 0))
        F.model_answer("BURNED_PERCENT", "40%")

    def file(self, quote=QUOTE, snap=SNAP, block=BLOCK, chain=1, token=TOKEN, sender=FILER, contract=None):
        return self.w.call(contract or self.bp, "file_claim", chain, token, snap, quote, block, sender=sender)

    def refused(self, code, **k):
        with self.assertRaises(world.Reverted) as cm:
            self.file(**k)
        self.assertTrue(cm.exception.msg.startswith("REFUSED: " + code), cm.exception.msg)
        return cm.exception.msg

    def verdict(self, expect, code=None, **k):
        r = self.file(**k)
        self.assertEqual(r["verdict"], expect, r)
        if code is not None:
            self.assertEqual(r["code"], code, r)
        return r

    def stats(self):
        return self.w.view(self.bp, "get_stats")


# ---------------------------------------------------------------- happy paths

class TestVerdicts(Base):
    def test_percent_true(self):
        r = self.verdict("TRUE", "BURNED_ENOUGH")
        c = self.w.view(self.bp, "get_check", r["check_id"])
        self.assertEqual(c["claim_type"], "BURNED_PERCENT")
        self.assertEqual(c["claim_text"], "40%")
        self.assertEqual(c["burned"], str(T(410)))
        self.assertEqual(c["total_supply"], str(T(1000)))
        self.assertEqual(c["host"], SITE)
        self.assertEqual(c["snapshot"], SNAP)
        self.assertEqual(c["block"], BLOCK)

    def test_percent_false(self):
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(300), 0))
        r = self.verdict("FALSE", "BURNED_SHORT")
        self.assertIn("30.0000%", r["why"])

    def test_amount_true(self):
        F.page("A total of 400 trillion tokens burned so far.")
        F.set_token(1, TOKEN, 18, T(10 ** 15), (0, 0, T(410 * 10 ** 12), 0))
        F.model_answer("BURNED_AMOUNT", "400", "trillion")
        self.verdict("TRUE", "BURNED_ENOUGH", quote="400 trillion tokens burned")

    def test_amount_false(self):
        F.page("A total of 400 trillion tokens burned so far.")
        F.set_token(1, TOKEN, 18, T(10 ** 15), (0, 0, T(300 * 10 ** 12), 0))
        F.model_answer("BURNED_AMOUNT", "400 trillion")
        self.verdict("FALSE", "BURNED_SHORT", quote="400 trillion tokens burned")

    def test_supply_true(self):
        F.page("Total Supply: 10,000,000,000,000 tokens")
        F.set_token(1, TOKEN, 9, T(10 ** 13, 9))
        F.model_answer("SUPPLY_AT_MOST", "10,000,000,000,000")
        self.verdict("TRUE", "SUPPLY_WITHIN", quote="Total Supply: 10,000,000,000,000")

    def test_supply_false(self):
        F.page("Total Supply: 10,000,000,000,000 tokens")
        F.set_token(1, TOKEN, 9, T(11 * 10 ** 12, 9))
        F.model_answer("SUPPLY_AT_MOST", "10,000,000,000,000")
        self.verdict("FALSE", "SUPPLY_ABOVE", quote="Total Supply: 10,000,000,000,000")

    def test_supply_with_no_dead_burns_still_decided(self):
        F.page("Total Supply: 10,000,000,000,000 tokens")
        F.set_token(1, TOKEN, 9, T(10 ** 13, 9))
        F.model_answer("SUPPLY_AT_MOST", "10,000,000,000,000")
        self.verdict("TRUE", quote="Total Supply: 10,000,000,000,000")

    def test_bsc_chain(self):
        F.set_token(56, TOKEN, 9, T(420 * 10 ** 15, 9), (0, 0, T(217 * 10 ** 15, 9), 0))
        self.verdict("TRUE", chain=56)

    def test_every_dead_address_counts(self):
        for i in range(4):
            dead = [0, 0, 0, 0]
            dead[i] = T(400)
            self.setUp()
            F.set_token(1, TOKEN, 18, T(1000), tuple(dead))
            self.verdict("TRUE")

    def test_dead_balances_are_summed(self):
        F.set_token(1, TOKEN, 18, T(1000), (T(100), T(100), T(100), T(100)))
        r = self.verdict("TRUE")
        c = self.w.view(self.bp, "get_check", r["check_id"])
        self.assertEqual(c["dead_balances"], [str(T(100))] * 4)
        self.assertEqual(c["burned"], str(T(400)))

    def test_other_holder_is_not_burned(self):
        # 40% held by a non-dead address does not count
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(10), 0))
        self.verdict("FALSE")

    def test_verdict_stores_explorer_links(self):
        r = self.file()
        c = self.w.view(self.bp, "get_check", r["check_id"])
        self.assertEqual(c["token_url"], "https://etherscan.io/token/" + TOKEN)
        self.assertEqual(c["block_url"], "https://etherscan.io/block/" + str(BLOCK))

    def test_bsc_explorer_links(self):
        F.set_token(56, TOKEN, 9, T(1000, 9), (0, 0, T(500, 9), 0))
        r = self.file(chain=56)
        c = self.w.view(self.bp, "get_check", r["check_id"])
        self.assertTrue(c["token_url"].startswith("https://bscscan.com/token/"))


# ---------------------------------------------------------------- tolerance

class TestTolerance(Base):
    def test_percent_exact_boundary_is_true(self):
        # 40% * 0.995 = 39.8%
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(398), 0))
        self.verdict("TRUE")

    def test_percent_one_wei_below_boundary_is_false(self):
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(398) - 1, 0))
        self.verdict("FALSE")

    def test_amount_exact_boundary_is_true(self):
        F.page("We burned 1,000,000 tokens.")
        F.model_answer("BURNED_AMOUNT", "1,000,000")
        F.set_token(1, TOKEN, 18, T(10 ** 9), (0, 0, T(995000), 0))
        self.verdict("TRUE", quote="We burned 1,000,000 tokens.")

    def test_amount_one_wei_below_boundary_is_false(self):
        F.page("We burned 1,000,000 tokens.")
        F.model_answer("BURNED_AMOUNT", "1,000,000")
        F.set_token(1, TOKEN, 18, T(10 ** 9), (0, 0, T(995000) - 1, 0))
        self.verdict("FALSE", quote="We burned 1,000,000 tokens.")

    def test_supply_exact_boundary_is_true(self):
        F.page("Max supply 1,000,000 tokens.")
        F.model_answer("SUPPLY_AT_MOST", "1,000,000")
        F.set_token(1, TOKEN, 18, T(1005000))
        self.verdict("TRUE", quote="Max supply 1,000,000 tokens.")

    def test_supply_one_wei_above_boundary_is_false(self):
        F.page("Max supply 1,000,000 tokens.")
        F.model_answer("SUPPLY_AT_MOST", "1,000,000")
        F.set_token(1, TOKEN, 18, T(1005000) + 1)
        self.verdict("FALSE", quote="Max supply 1,000,000 tokens.")

    def test_fractional_percent_boundary(self):
        F.page("Percent burned: 7.82% of supply")
        F.model_answer("BURNED_PERCENT", "7.82%")
        # 7.82 * 0.995 = 7.7809 % of 10^6 = 77809
        F.set_token(1, TOKEN, 0, 10 ** 6, (0, 0, 77809, 0))
        self.verdict("TRUE", quote="Percent burned: 7.82%")

    def test_fractional_percent_just_below(self):
        F.page("Percent burned: 7.82% of supply")
        F.model_answer("BURNED_PERCENT", "7.82%")
        F.set_token(1, TOKEN, 0, 10 ** 6, (0, 0, 77808, 0))
        self.verdict("FALSE", quote="Percent burned: 7.82%")

    def test_supply_below_claim_is_true(self):
        F.page("Max supply 1,000,000 tokens.")
        F.model_answer("SUPPLY_AT_MOST", "1,000,000")
        F.set_token(1, TOKEN, 18, T(500000))
        self.verdict("TRUE", quote="Max supply 1,000,000 tokens.")

    def test_burned_far_above_claim_is_true(self):
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(999), 0))
        self.verdict("TRUE")


# ---------------------------------------------------------------- decimals

class TestDecimals(Base):
    def _amount(self, dec, burned):
        F.page("We burned 1.5 billion tokens.")
        F.model_answer("BURNED_AMOUNT", "1.5 billion")
        F.set_token(1, TOKEN, dec, T(10 ** 10, dec), (0, 0, burned, 0))
        return self.file(quote="We burned 1.5 billion tokens.")

    def test_dec_0(self):
        self.assertEqual(self._amount(0, 1500000000)["verdict"], "TRUE")

    def test_dec_6(self):
        self.assertEqual(self._amount(6, 1500000000 * 10 ** 6)["verdict"], "TRUE")

    def test_dec_9(self):
        self.assertEqual(self._amount(9, 1500000000 * 10 ** 9)["verdict"], "TRUE")

    def test_dec_18(self):
        self.assertEqual(self._amount(18, 1500000000 * 10 ** 18)["verdict"], "TRUE")

    def test_dec_9_read_as_18_would_be_false(self):
        # the right decimals matter: 1.5e9 tokens at 9 decimals is TRUE, the same
        # raw number at 18 decimals is only 1.5 tokens
        self.assertEqual(self._amount(18, 1500000000 * 10 ** 9)["verdict"], "FALSE")

    def test_dec_36_allowed(self):
        self.assertEqual(self._amount(36, 1500000000 * 10 ** 36)["verdict"], "TRUE")

    def test_dec_37_unverifiable(self):
        r = self._amount(37, 1500000000 * 10 ** 37)
        self.assertEqual((r["verdict"], r["code"]), ("UNVERIFIABLE", "TOKEN_UNREADABLE"))

    def test_percent_independent_of_decimals(self):
        for dec in (0, 6, 9, 18):
            self.setUp()
            F.set_token(1, TOKEN, dec, T(1000, dec), (0, 0, T(400, dec), 0))
            self.verdict("TRUE")

    def test_supply_dec_9(self):
        F.page("Total Supply: 10,000,000,000,000 tokens")
        F.model_answer("SUPPLY_AT_MOST", "10,000,000,000,000")
        F.set_token(1, TOKEN, 9, T(10 ** 13, 18))  # read with the wrong scale -> above
        self.verdict("FALSE", quote="Total Supply: 10,000,000,000,000")


# ---------------------------------------------------------------- number formats

def _num_case(quote, expect):
    def t(self):
        got = BP.claim_number(quote)
        if expect is None:
            self.assertIn("code", got, (quote, got))
        elif isinstance(expect, str):
            self.assertEqual(got.get("code"), expect, (quote, got))
        else:
            self.assertIn("ok", got, (quote, got))
            self.assertEqual((got["ok"][1], got["ok"][2], got["ok"][3]), expect, (quote, got))
    return t


NUM_CASES = {
    "trillion_word": ("400 trillion tokens burned", (400 * 10 ** 12, 1, "scaled")),
    "trillion_capital": ("400 Trillion tokens burned", (400 * 10 ** 12, 1, "scaled")),
    "quadrillion": ("a 420 Quadrillion supply", (420 * 10 ** 15, 1, "scaled")),
    "billion_decimal": ("1.5 billion burned", (15 * 10 ** 8, 1, "scaled")),
    "million": ("burned 25 million tokens", (25 * 10 ** 6, 1, "scaled")),
    "thousand": ("burned 750 thousand tokens", (750000, 1, "scaled")),
    "suffix_T": ("400T tokens burned", (400 * 10 ** 12, 1, "scaled")),
    "suffix_t_lower": ("400t burned so far", (400 * 10 ** 12, 1, "scaled")),
    "suffix_B": ("2B burned so far", (2 * 10 ** 9, 1, "scaled")),
    "suffix_M": ("3.5M burned so far", (35 * 10 ** 5, 1, "scaled")),
    "suffix_K": ("burned 50K of them", (50000, 1, "scaled")),
    "commas": ("400,000,000,000,000 tokens burned", (400 * 10 ** 12, 1, "plain")),
    "commas_decimal": ("burned 1,234,567.5 tokens", (2469135, 2, "plain")),
    "plain_digits": ("burned 400000000 tokens", (400000000, 1, "plain")),
    "percent": ("50% burned", (50, 1, "pct")),
    "percent_space": ("50 % burned", (50, 1, "pct")),
    "percent_word": ("50 percent burned", (50, 1, "pct")),
    "percent_decimal": ("Percent burned: 7.82%", (391, 50, "pct")),
    "percent_plus": ("We have burned 41%+ of the supply.", (41, 1, "pct")),
    "percent_end": ("the share burned is 41%", (41, 1, "pct")),
    "ten_thousand_is_shaped": ("burned 10,000 tokens", (10000, 1, "plain")),
    "year_not_shaped": ("In 2021 we burned 40% of supply", (40, 1, "pct")),
    "date_not_shaped": ("On May 17, 2021 we burned 40% of supply", (40, 1, "pct")),
    "small_count_not_shaped": ("12 holders saw 40% burned", (40, 1, "pct")),
    "covid_19": ("For Covid-19 relief we burned 40% of supply", (40, 1, "pct")),
    "9999_not_shaped": ("9,999 wallets watched 40% burn", (40, 1, "pct")),
    "two_percents": ("40% burned and 10% locked", "MULTIPLE_CLAIM_NUMBERS"),
    "percent_and_amount": ("Starting with a supply of 1 quadrillion, locked 50% in Uniswap", "MULTIPLE_CLAIM_NUMBERS"),
    "two_amounts": ("burned 400 trillion of 1 quadrillion", "MULTIPLE_CLAIM_NUMBERS"),
    "amount_and_big_plain": ("burned 400T of 1,000,000,000,000,000", "MULTIPLE_CLAIM_NUMBERS"),
    "same_number_twice": ("40% burned, yes 40%", "MULTIPLE_CLAIM_NUMBERS"),
    "no_number": ("we burned half of the supply", "NO_CLAIM_NUMBER"),
    "only_year": ("we burned tokens in 2021", "NO_CLAIM_NUMBER"),
    "fullwidth_digits": ("we burned ４０% of supply", "NON_ASCII_DIGITS"),
    "fullwidth_percent": ("we burned 40％ of supply", "NON_ASCII_DIGITS"),
    "arabic_digits": ("we burned ٤٠% of supply", "NON_ASCII_DIGITS"),
    "superscript_digit": ("we burned 40% of supply²", "NON_ASCII_DIGITS"),
    "per_mille": ("we burned 40‰ of supply", "NON_ASCII_DIGITS"),
    "european_dots": ("burned 400.000.000 tokens", "NO_CLAIM_NUMBER"),
    "hex_address_ignored": ("40% sent to 0x000000000000000000000000000000000000dEaD", (40, 1, "pct")),
    "version_ignored": ("v2 burned 40% of supply", (40, 1, "pct")),
    "dollar_value": ("burned 40% worth $1,000,000", "MULTIPLE_CLAIM_NUMBERS"),
    "word_glued": ("burned 400trillion", "NO_CLAIM_NUMBER"),
    "suffix_in_word": ("burned 40 Tokens", "NO_CLAIM_NUMBER"),
    "leading_zero": ("burned 040% of supply", (40, 1, "pct")),
    "percent_of_percent": ("burned 0.5% of supply", (1, 2, "pct")),
}

class TestNumberFormats(unittest.TestCase):
    pass


for _name, (_q, _e) in NUM_CASES.items():
    setattr(TestNumberFormats, "test_" + _name, _num_case(_q, _e))


class TestNumberFormatsOnChain(Base):
    """The accepted forms end to end, against the same chain state."""

    def _go(self, page_text, quote, t, number, unit, burned):
        F.page(page_text)
        F.model_answer(t, number, unit)
        F.set_token(1, TOKEN, 18, T(10 ** 15), (0, 0, burned, 0))
        return self.file(quote=quote)

    def test_words(self):
        r = self._go("we burned 400 trillion tokens", "burned 400 trillion tokens", "BURNED_AMOUNT", "400", "trillion", T(400 * 10 ** 12))
        self.assertEqual(r["verdict"], "TRUE")

    def test_suffix(self):
        r = self._go("we burned 400T tokens", "burned 400T tokens", "BURNED_AMOUNT", "400T", "", T(400 * 10 ** 12))
        self.assertEqual(r["verdict"], "TRUE")

    def test_commas(self):
        r = self._go("we burned 400,000,000,000,000 tokens", "burned 400,000,000,000,000 tokens", "BURNED_AMOUNT",
                     "400,000,000,000,000", "tokens", T(400 * 10 ** 12))
        self.assertEqual(r["verdict"], "TRUE")

    def test_percent(self):
        r = self._go("we burned 50% of supply", "burned 50% of supply", "BURNED_PERCENT", "50%", "", T(5 * 10 ** 14))
        self.assertEqual(r["verdict"], "TRUE")

    def test_percent_unit_split(self):
        r = self._go("we burned 50% of supply", "burned 50% of supply", "BURNED_PERCENT", "50", "%", T(5 * 10 ** 14))
        self.assertEqual(r["verdict"], "TRUE")

    def test_percent_word_unit(self):
        r = self._go("we burned 50 percent of supply", "burned 50 percent of supply", "BURNED_PERCENT", "50", "percent", T(5 * 10 ** 14))
        self.assertEqual(r["verdict"], "TRUE")

    def test_multi_number_quote_is_unverifiable(self):
        r = self._go("we burned 50% of 1 quadrillion", "burned 50% of 1 quadrillion", "BURNED_PERCENT", "50%", "", T(5 * 10 ** 14))
        self.assertEqual((r["verdict"], r["code"]), ("UNVERIFIABLE", "MULTIPLE_CLAIM_NUMBERS"))

    def test_multi_number_quote_never_asks_the_model(self):
        self._go("we burned 50% of 1 quadrillion", "burned 50% of 1 quadrillion", "BURNED_PERCENT", "50%", "", 0)
        self.assertEqual(stub.MODEL.prompts, [])

    def test_no_number_is_unverifiable(self):
        r = self._go("we burned half of the supply", "burned half of the supply", "BURNED_PERCENT", "50%", "", 0)
        self.assertEqual(r["code"], "NO_CLAIM_NUMBER")


# ---------------------------------------------------------------- model output

class TestModelOutput(Base):
    def _r(self, answer):
        stub.MODEL.answer = answer
        return self.file()

    def test_number_not_in_quote(self):
        r = self._r({"type": "BURNED_PERCENT", "number": "41%", "unit": ""})
        self.assertEqual(r["code"], "MODEL_OUTPUT_INVALID")

    def test_number_value_differs(self):
        r = self._r({"type": "BURNED_PERCENT", "number": "4", "unit": "%"})
        self.assertEqual(r["code"], "MODEL_OUTPUT_INVALID")

    def test_type_not_in_enum(self):
        r = self._r({"type": "BURNED_SOME", "number": "40%", "unit": ""})
        self.assertEqual(r["code"], "MODEL_OUTPUT_INVALID")

    def test_type_none(self):
        r = self._r({"type": "NONE", "number": "", "unit": ""})
        self.assertEqual(r["code"], "NOT_A_BURN_CLAIM")

    def test_percent_number_with_amount_type(self):
        r = self._r({"type": "BURNED_AMOUNT", "number": "40%", "unit": ""})
        self.assertEqual(r["code"], "MODEL_OUTPUT_INVALID")

    def test_percent_type_with_plain_number(self):
        F.page("we burned 400,000 tokens so far")
        F.model_answer("BURNED_PERCENT", "400,000")
        r = self.file(quote="burned 400,000 tokens so far")
        self.assertEqual(r["code"], "MODEL_OUTPUT_INVALID")

    def test_number_missing(self):
        r = self._r({"type": "BURNED_PERCENT", "unit": "%"})
        self.assertEqual(r["code"], "MODEL_OUTPUT_INVALID")

    def test_number_not_string(self):
        r = self._r({"type": "BURNED_PERCENT", "number": 40, "unit": "%"})
        self.assertEqual(r["code"], "MODEL_OUTPUT_INVALID")

    def test_not_a_dict(self):
        r = self._r(["BURNED_PERCENT", "40%"])
        self.assertEqual(r["code"], "MODEL_OUTPUT_INVALID")

    def test_json_string_accepted(self):
        r = self._r(json.dumps({"type": "BURNED_PERCENT", "number": "40%", "unit": ""}))
        self.assertEqual(r["verdict"], "TRUE")

    def test_garbage_string(self):
        r = self._r("I think it is 40%")
        self.assertEqual(r["code"], "MODEL_OUTPUT_INVALID")

    def test_lowercase_type_accepted(self):
        r = self._r({"type": "burned_percent", "number": "40%", "unit": ""})
        self.assertEqual(r["verdict"], "TRUE")

    def test_model_unavailable(self):
        stub.MODEL.raise_next = 1
        r = self.file()
        self.assertEqual(r["code"], "MODEL_UNAVAILABLE")

    def test_readings_differ(self):
        F.page("We burned 1,000,000 tokens.")
        F.set_token(1, TOKEN, 18, T(10 ** 9), (0, 0, T(10 ** 6), 0))
        stub.MODEL.answer = [{"type": "BURNED_AMOUNT", "number": "1,000,000", "unit": ""},
                             {"type": "SUPPLY_AT_MOST", "number": "1,000,000", "unit": ""}]
        r = self.file(quote="We burned 1,000,000 tokens.")
        self.assertEqual((r["verdict"], r["code"]), ("UNVERIFIABLE", "READINGS_DIFFER"))

    def test_two_readings_are_asked(self):
        self.file()
        # leader reads twice; the validator reads once
        self.assertEqual(len(stub.MODEL.prompts), 3)

    def test_prompt_holds_only_the_quote(self):
        self.file()
        p = stub.MODEL.prompts[0]
        self.assertIn(QUOTE, p)
        self.assertNotIn("dead wallet", p)  # the rest of the page never reaches the model
        self.assertNotIn(TOKEN, p)

    def test_unit_scale_mismatch(self):
        F.page("A total of 400 trillion tokens burned so far.")
        F.model_answer("BURNED_AMOUNT", "400", "billion")
        r = self.file(quote="400 trillion tokens burned")
        self.assertEqual(r["code"], "MODEL_OUTPUT_INVALID")

    def test_unit_missing_scale(self):
        F.page("A total of 400 trillion tokens burned so far.")
        F.model_answer("BURNED_AMOUNT", "400", "")
        r = self.file(quote="400 trillion tokens burned")
        self.assertEqual(r["code"], "MODEL_OUTPUT_INVALID")

    def test_two_scale_words(self):
        F.page("A total of 400 trillion tokens burned so far.")
        F.model_answer("BURNED_AMOUNT", "400", "trillion billion")
        r = self.file(quote="400 trillion tokens burned")
        self.assertEqual(r["code"], "MODEL_OUTPUT_INVALID")

    def test_number_too_long(self):
        r = self._r({"type": "BURNED_PERCENT", "number": "40%" + " " * 2 + "x" * 50, "unit": ""})
        self.assertEqual(r["code"], "MODEL_OUTPUT_INVALID")

    def test_empty_number(self):
        r = self._r({"type": "BURNED_PERCENT", "number": "  ", "unit": ""})
        self.assertEqual(r["code"], "MODEL_OUTPUT_INVALID")

    def test_model_number_holding_two_numbers(self):
        F.page("burned 40% now, 50% soon")
        r = self._r({"type": "BURNED_PERCENT", "number": "40% now, 50%", "unit": ""})
        self.assertEqual(r["verdict"], "UNVERIFIABLE")

    def test_model_type_cannot_override_code_number(self):
        # the model may say SUPPLY for a percent quote: refused by code
        r = self._r({"type": "SUPPLY_AT_MOST", "number": "40%", "unit": ""})
        self.assertEqual(r["code"], "MODEL_OUTPUT_INVALID")

    def test_model_unit_tokens_ignored(self):
        F.page("we burned 400,000 tokens so far")
        F.set_token(1, TOKEN, 18, T(10 ** 9), (0, 0, T(400000), 0))
        F.model_answer("BURNED_AMOUNT", "400,000", "tokens")
        self.assertEqual(self.file(quote="burned 400,000 tokens so far")["verdict"], "TRUE")


# ---------------------------------------------------------------- the archived page

class TestPage(Base):
    def test_quote_not_on_page(self):
        r = self.verdict("UNVERIFIABLE", "QUOTE_NOT_ON_PAGE", quote="burned 50% of the total supply")
        self.assertEqual(r["check_id"], 1)

    def test_case_sensitive(self):
        self.verdict("UNVERIFIABLE", "QUOTE_NOT_ON_PAGE", quote="Burned 40% of the total supply")

    def test_whitespace_normalized_in_quote(self):
        self.verdict("TRUE", quote="burned   40%\n of the\ttotal supply")

    def test_whitespace_normalized_in_page(self):
        F.page("we have burned\n\n  40%    of the\n total supply")
        self.verdict("TRUE")

    def test_quote_across_tags(self):
        F.page("we have burned <b>40%</b> of the <span>total supply</span>")
        self.verdict("TRUE")

    def test_entities_decoded(self):
        F.page("we&nbsp;have burned 40&#37; of the total&#x20;supply")
        self.verdict("TRUE")

    def test_text_in_script_does_not_count(self):
        F.page("<html><body><script>var t = 'burned 40% of the total supply';</script><p>hello there</p></body></html>")
        self.verdict("UNVERIFIABLE", "QUOTE_NOT_ON_PAGE")

    def test_text_in_style_does_not_count(self):
        F.page("<html><head><style>/* burned 40% of the total supply */</style></head><body>x</body></html>")
        self.verdict("UNVERIFIABLE", "QUOTE_NOT_ON_PAGE")

    def test_text_in_comment_does_not_count(self):
        F.page("<html><body><!-- burned 40% of the total supply --><p>x</p></body></html>")
        self.verdict("UNVERIFIABLE", "QUOTE_NOT_ON_PAGE")

    def test_text_in_attribute_does_not_count(self):
        F.page('<html><body><img alt="burned 40% of the total supply"><p>x</p></body></html>')
        self.verdict("UNVERIFIABLE", "QUOTE_NOT_ON_PAGE")

    def test_text_in_noscript_does_not_count(self):
        F.page("<html><body><noscript>burned 40% of the total supply</noscript><p>x</p></body></html>")
        self.verdict("UNVERIFIABLE", "QUOTE_NOT_ON_PAGE")

    def test_http_404(self):
        F.page(PAGE, status=404)
        self.verdict("UNVERIFIABLE", "PAGE_UNAVAILABLE")

    def test_http_500(self):
        F.page(PAGE, status=500)
        self.verdict("UNVERIFIABLE", "PAGE_UNAVAILABLE")

    def test_page_missing(self):
        stub.WEB.pages.clear()
        self.verdict("UNVERIFIABLE", "PAGE_UNAVAILABLE")

    def test_archive_timeout(self):
        stub.WEB.down.add(F.RAW)
        self.verdict("UNVERIFIABLE", "PAGE_UNAVAILABLE")

    def test_other_capture_served(self):
        F.page(PAGE, memento_ts="20211224103600")
        self.verdict("UNVERIFIABLE", "SNAPSHOT_MISMATCH")

    def test_no_memento_header(self):
        F.page(PAGE, headers={"content-type": "text/html"})
        self.verdict("UNVERIFIABLE", "SNAPSHOT_MISMATCH")

    def test_other_host_captured(self):
        F.page(PAGE, original="https://evil.example/")
        self.verdict("UNVERIFIABLE", "SNAPSHOT_MISMATCH")

    def test_http_original_same_host_ok(self):
        F.page(PAGE, original="http://" + SITE + "/")
        self.verdict("TRUE")

    def test_page_too_large(self):
        F.page("x" * (BP.MAX_PAGE + 10) + PAGE)
        self.verdict("UNVERIFIABLE", "PAGE_UNAVAILABLE")

    def test_page_fetched_by_raw_id_url(self):
        self.file()
        self.assertIn(F.RAW, stub.WEB.log)
        self.assertNotIn(SNAP, stub.WEB.log)

    def test_no_chain_read_when_quote_missing(self):
        stub.WEB.log.clear()
        self.file(quote="burned 50% of the total supply")
        self.assertFalse(any(u in stub.WEB.log for u in (F.ETH_A, F.ETH_B)))

    def test_non_utf8_bytes_tolerated(self):
        stub.WEB.pages[F.RAW] = (200, b"<p>we have burned 40% of the total supply \xff\xfe</p>",
                                  {"memento-datetime": F.memento(TS), "link": '<https://' + SITE + '/>; rel="original"'})
        self.verdict("TRUE")


# ---------------------------------------------------------------- the snapshot URL (door)

def _url_case(url, code):
    def t(self):
        if code is None:
            self.assertIsInstance(BP.parse_snapshot(url), dict, url)
        else:
            got = BP.parse_snapshot(url)
            self.assertEqual(got, code, url)
    return t


URL_CASES = {
    "valid": ("https://web.archive.org/web/20211224103559/https://example.io/", None),
    "valid_path_query": ("https://web.archive.org/web/20211224103559/https://example.io/burn?x=1", None),
    "valid_http_original": ("https://web.archive.org/web/20211224103559/http://example.io/", None),
    "plain_site": ("https://example.io/", "NOT_ARCHIVE_URL"),
    "http_archive": ("http://web.archive.org/web/20211224103559/https://example.io/", "NOT_ARCHIVE_URL"),
    "archive_ph": ("https://archive.ph/20211224103559/https://example.io/", "NOT_ARCHIVE_URL"),
    "lookalike_domain": ("https://web.archive.org.evil.io/web/20211224103559/https://example.io/", "NOT_ARCHIVE_URL"),
    "userinfo": ("https://web.archive.org@evil.io/web/20211224103559/https://example.io/", "NOT_ARCHIVE_URL"),
    "uppercase_host": ("https://WEB.ARCHIVE.ORG/web/20211224103559/https://example.io/", "NOT_ARCHIVE_URL"),
    "port": ("https://web.archive.org:443/web/20211224103559/https://example.io/", "NOT_ARCHIVE_URL"),
    "subdomain": ("https://wayback.archive.org/web/20211224103559/https://example.io/", "NOT_ARCHIVE_URL"),
    "cyrillic_a": ("https://web.аrchive.org/web/20211224103559/https://example.io/", "NOT_ARCHIVE_URL"),
    "backslash": ("https://web.archive.org/web/20211224103559/https:\\\\example.io/", "NOT_ARCHIVE_URL"),
    "space_inside": ("https://web.archive.org/web/20211224103559/https://exa mple.io/", "NOT_ARCHIVE_URL"),
    "fragment": ("https://web.archive.org/web/20211224103559/https://example.io/#x", "NOT_ARCHIVE_URL"),
    "original_is_archive": ("https://web.archive.org/web/20211224103559/https://web.archive.org/x", "NOT_ARCHIVE_URL"),
    "original_is_archive_sub": ("https://web.archive.org/web/20211224103559/https://blog.archive.org/x", "NOT_ARCHIVE_URL"),
    "original_ftp": ("https://web.archive.org/web/20211224103559/ftp://example.io/", "NOT_ARCHIVE_URL"),
    "original_no_dot": ("https://web.archive.org/web/20211224103559/https://localhost/", "NOT_ARCHIVE_URL"),
    "original_userinfo": ("https://web.archive.org/web/20211224103559/https://a@b.io/", "NOT_ARCHIVE_URL"),
    "ts_13": ("https://web.archive.org/web/2021122410355/https://example.io/", "BAD_TIMESTAMP"),
    "ts_15": ("https://web.archive.org/web/202112241035590/https://example.io/", "BAD_TIMESTAMP"),
    "ts_year_only": ("https://web.archive.org/web/2021/https://example.io/", "BAD_TIMESTAMP"),
    "ts_star": ("https://web.archive.org/web/*/https://example.io/", "BAD_TIMESTAMP"),
    "ts_id_modifier": ("https://web.archive.org/web/20211224103559id_/https://example.io/", "BAD_TIMESTAMP"),
    "ts_month_13": ("https://web.archive.org/web/20211324103559/https://example.io/", "BAD_TIMESTAMP"),
    "ts_feb_30": ("https://web.archive.org/web/20210230103559/https://example.io/", "BAD_TIMESTAMP"),
    "ts_feb_29_nonleap": ("https://web.archive.org/web/20210229103559/https://example.io/", "BAD_TIMESTAMP"),
    "ts_hour_24": ("https://web.archive.org/web/20211224243559/https://example.io/", "BAD_TIMESTAMP"),
    "ts_minute_60": ("https://web.archive.org/web/20211224106059/https://example.io/", "BAD_TIMESTAMP"),
    "ts_second_60": ("https://web.archive.org/web/20211224103560/https://example.io/", "BAD_TIMESTAMP"),
    "ts_before_archive": ("https://web.archive.org/web/19951224103559/https://example.io/", "BAD_TIMESTAMP"),
    "ts_letters": ("https://web.archive.org/web/2021122410355a/https://example.io/", "BAD_TIMESTAMP"),
    "ts_missing": ("https://web.archive.org/web/", "BAD_TIMESTAMP"),
    "too_long": ("https://web.archive.org/web/20211224103559/https://example.io/" + "a" * 700, "URL_TOO_LONG"),
}


class TestSnapshotUrl(unittest.TestCase):
    pass


for _name, (_u, _c) in URL_CASES.items():
    setattr(TestSnapshotUrl, "test_" + _name, _url_case(_u, _c))


class TestDoor(Base):
    def test_non_archive_url_refused(self):
        self.refused("NOT_ARCHIVE_URL", snap="https://example-token.io/")

    def test_bad_timestamp_refused(self):
        self.refused("BAD_TIMESTAMP", snap="https://web.archive.org/web/2021/https://example-token.io/")

    def test_future_timestamp_refused(self):
        self.refused("BAD_TIMESTAMP", snap=F.snap_url("20301224103559"))

    def test_feb_29_leap_year_ok(self):
        F.page(PAGE, ts="20240229103559")
        self.verdict("TRUE", snap=F.snap_url("20240229103559"))

    def test_unsupported_chain(self):
        self.refused("UNSUPPORTED_CHAIN", chain=137)

    def test_chain_not_int(self):
        self.refused("UNSUPPORTED_CHAIN", chain="eth")

    def test_token_short(self):
        self.refused("BAD_TOKEN_ADDRESS", token="0x1234")

    def test_token_not_hex(self):
        self.refused("BAD_TOKEN_ADDRESS", token="0x" + "g" * 40)

    def test_token_no_prefix(self):
        self.refused("BAD_TOKEN_ADDRESS", token="1" * 42)

    def test_token_is_dead_address(self):
        self.refused("BAD_TOKEN_ADDRESS", token="0x000000000000000000000000000000000000dEaD")

    def test_token_mixed_case_ok(self):
        self.verdict("TRUE", token=TOKEN.upper().replace("0X", "0x"))

    def test_quote_too_short(self):
        self.refused("BAD_QUOTE", quote="40% burned")

    def test_quote_too_long(self):
        self.refused("BAD_QUOTE", quote="burned 40% " + "x" * 400)

    def test_quote_control_char(self):
        self.refused("BAD_QUOTE", quote="burned 40% of\x00 the total supply")

    def test_quote_not_string(self):
        self.refused("BAD_QUOTE", quote=40)

    def test_block_zero(self):
        self.refused("BAD_BLOCK", block=0)

    def test_block_negative(self):
        self.refused("BAD_BLOCK", block=-5)

    def test_block_huge(self):
        self.refused("BAD_BLOCK", block=10 ** 12)

    def test_block_not_int(self):
        self.refused("BAD_BLOCK", block="latest")

    def test_refusal_stores_nothing(self):
        before = self.stats()
        self.refused("NOT_ARCHIVE_URL", snap="https://example-token.io/")
        self.assertEqual(self.stats(), before)
        self.assertFalse(self.w.view(self.bp, "get_check", 1)["found"])

    def test_refusal_reads_nothing(self):
        stub.WEB.log.clear()
        self.refused("BAD_TIMESTAMP", snap="https://web.archive.org/web/2021/https://example-token.io/")
        self.assertEqual(stub.WEB.log, [])
        self.assertEqual(stub.MODEL.prompts, [])

    def test_no_clock(self):
        self.w.now_iso = ""
        self.refused("NO_CLOCK")


# ---------------------------------------------------------------- the chain read

class TestChain(Base):
    def test_rpc_disagree_supply(self):
        F.set_token(1, TOKEN, 18, T(1001), (0, 0, T(410), 0), urls=[F.ETH_B])
        self.verdict("UNVERIFIABLE", "RPC_DISAGREE")

    def test_rpc_disagree_dead_balance(self):
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(410) + 1, 0), urls=[F.ETH_B])
        self.verdict("UNVERIFIABLE", "RPC_DISAGREE")

    def test_rpc_disagree_decimals(self):
        F.set_token(1, TOKEN, 9, T(1000), (0, 0, T(410), 0), urls=[F.ETH_B])
        self.verdict("UNVERIFIABLE", "RPC_DISAGREE")

    def test_rpc_disagree_block_hash(self):
        stub.WEB.chains[F.ETH_B].blocks[BLOCK] = ("0x" + "ab" * 32, F.BLOCK_TS)
        self.verdict("UNVERIFIABLE", "RPC_DISAGREE")

    def test_rpc_disagree_block_time(self):
        stub.WEB.chains[F.ETH_B].blocks[BLOCK] = (stub.WEB.chains[F.ETH_A].blocks[BLOCK][0], F.BLOCK_TS + 1)
        self.verdict("UNVERIFIABLE", "RPC_DISAGREE")

    def test_rpc_a_down(self):
        stub.WEB.down.add(F.ETH_A)
        self.verdict("UNVERIFIABLE", "RPC_UNAVAILABLE")

    def test_rpc_b_down(self):
        stub.WEB.down.add(F.ETH_B)
        self.verdict("UNVERIFIABLE", "RPC_UNAVAILABLE")

    def test_rpc_http_500(self):
        stub.WEB.rpc_status[F.ETH_B] = 500
        self.verdict("UNVERIFIABLE", "RPC_UNAVAILABLE")

    def test_rpc_429(self):
        stub.WEB.rpc_status[F.ETH_A] = 429
        self.verdict("UNVERIFIABLE", "RPC_UNAVAILABLE")

    def test_rpc_error_answer(self):
        stub.WEB.chains[F.ETH_A].fail = lambda m, p: {"code": -32000, "message": "missing trie node"} if m == "eth_call" else None
        self.verdict("UNVERIFIABLE", "RPC_UNAVAILABLE")

    def test_balance_reverts(self):
        for url in (F.ETH_A, F.ETH_B):
            stub.WEB.chains[url].calls[(TOKEN, "0x70a08231" + "0" * 24 + F.DEAD[0][2:])] = stub.MockChain.REVERT
        self.verdict("UNVERIFIABLE", "RPC_UNAVAILABLE")

    def test_short_return_word(self):
        for url in (F.ETH_A, F.ETH_B):
            stub.WEB.chains[url].calls[(TOKEN, "0x18160ddd")] = "0x01"
        self.verdict("UNVERIFIABLE", "RPC_UNAVAILABLE")

    def test_wrong_chain_id(self):
        stub.WEB.chains[F.ETH_A].chain_id = 5
        self.verdict("UNVERIFIABLE", "RPC_UNAVAILABLE")

    def test_block_not_finalized_on_one(self):
        stub.WEB.chains[F.ETH_B].finalized = BLOCK - 1
        stub.WEB.chains[F.ETH_B].set_block(BLOCK - 1, F.BLOCK_TS - 12)
        self.verdict("UNVERIFIABLE", "BLOCK_NOT_FINALIZED")

    def test_block_unknown(self):
        self.verdict("UNVERIFIABLE", "RPC_UNAVAILABLE", block=BLOCK + 5)

    def test_block_before_snapshot(self):
        stub.WEB.chains[F.ETH_A].blocks[BLOCK] = (stub.WEB.chains[F.ETH_A].blocks[BLOCK][0], 1600000000)
        stub.WEB.chains[F.ETH_B].blocks[BLOCK] = stub.WEB.chains[F.ETH_A].blocks[BLOCK]
        self.verdict("UNVERIFIABLE", "BLOCK_BEFORE_SNAPSHOT")

    def test_not_a_contract(self):
        self.verdict("UNVERIFIABLE", "TOKEN_UNREADABLE", token=F.addr(999))

    def test_zero_supply(self):
        F.set_token(1, TOKEN, 18, 0, (0, 0, 0, 0))
        self.verdict("UNVERIFIABLE", "TOKEN_UNREADABLE")

    def test_burned_above_supply(self):
        F.set_token(1, TOKEN, 18, T(1000), (T(600), 0, T(600), 0))
        self.verdict("UNVERIFIABLE", "TOKEN_UNREADABLE")

    def test_no_dead_burns_percent(self):
        F.set_token(1, TOKEN, 18, T(1000))
        self.verdict("UNVERIFIABLE", "NO_DEAD_ADDRESS_BURNS")

    def test_no_dead_burns_amount(self):
        F.page("We burned 1,000,000 tokens.")
        F.model_answer("BURNED_AMOUNT", "1,000,000")
        F.set_token(1, TOKEN, 18, T(10 ** 9))
        self.verdict("UNVERIFIABLE", "NO_DEAD_ADDRESS_BURNS", quote="We burned 1,000,000 tokens.")

    def test_reads_at_the_pinned_block(self):
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(100), 0))          # latest state: 10%
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(410), 0), block=BLOCK)  # at the block: 41%
        self.verdict("TRUE")

    def test_every_call_names_the_block(self):
        self.file()
        for m, p in stub.WEB.chains[F.ETH_A].log:
            params = json.loads(p)
            if m in ("eth_call", "eth_getCode"):
                self.assertEqual(params[-1], hex(BLOCK))

    def test_both_rpcs_are_read(self):
        self.file()
        self.assertTrue(stub.WEB.chains[F.ETH_A].log)
        self.assertTrue(stub.WEB.chains[F.ETH_B].log)

    def test_bsc_uses_bsc_rpcs(self):
        F.set_token(56, TOKEN, 9, T(1000, 9), (0, 0, T(500, 9), 0))
        self.file(chain=56)
        self.assertTrue(stub.WEB.chains[F.BSC_A].log)
        self.assertFalse(stub.WEB.chains[F.ETH_A].log)

    def test_record_holds_block_hash_and_time(self):
        r = self.file()
        c = self.w.view(self.bp, "get_check", r["check_id"])
        self.assertEqual(c["block_hash"], stub.WEB.chains[F.ETH_A].blocks[BLOCK][0])
        self.assertEqual(c["block_time"], F.BLOCK_TS)


# ---------------------------------------------------------------- duplicate / rate limit / counters

class TestLimits(Base):
    def test_duplicate_refused(self):
        self.file()
        msg = self.refused("DUPLICATE_OF_1")
        self.assertIn("1", msg)

    def test_duplicate_from_other_sender_refused(self):
        self.file()
        self.refused("DUPLICATE_OF_1", sender=FILER2)

    def test_duplicate_with_whitespace_variant_refused(self):
        self.file()
        self.refused("DUPLICATE_OF_1", quote="burned  40%  of the total supply")

    def test_duplicate_of_unverifiable_refused(self):
        self.file(quote="burned 50% of the total supply")
        self.refused("DUPLICATE_OF_1", quote="burned 50% of the total supply")

    def test_duplicate_token_case_refused(self):
        self.file()
        self.refused("DUPLICATE_OF_1", token=TOKEN.upper().replace("0X", "0x"))

    def test_other_block_not_duplicate(self):
        stub.WEB.chains[F.ETH_A].set_block(BLOCK + 1, F.BLOCK_TS + 12)
        stub.WEB.chains[F.ETH_B].set_block(BLOCK + 1, F.BLOCK_TS + 12)
        self.file()
        self.assertEqual(self.file(block=BLOCK + 1)["check_id"], 2)

    def test_other_quote_not_duplicate(self):
        self.file()
        self.assertEqual(self.file(quote="has burned 40% of the total supply")["check_id"], 2)

    def test_rate_limit(self):
        for i in range(5):
            self.file(quote=QUOTE if i == 0 else "x" * i + " never on the page")
        self.refused("RATE_LIMITED_UNTIL_" + str(NOW + 3600), quote="another quote not on page")

    def test_rate_limit_per_sender(self):
        for i in range(5):
            self.file(quote="quote number " + "x" * i)
        self.assertEqual(self.file(sender=FILER2)["verdict"], "TRUE")

    def test_rate_limit_window_resets(self):
        for i in range(5):
            self.file(quote="quote number " + "x" * i)
        self.w.advance(3600)
        self.assertEqual(self.file()["verdict"], "TRUE")

    def test_rate_limit_counts_only_stored(self):
        for i in range(10):
            with self.assertRaises(world.Reverted):
                self.file(snap="https://bad.example/")
        self.assertEqual(self.file()["verdict"], "TRUE")

    def test_rate_status_view(self):
        self.file()
        rs = self.w.view(self.bp, "rate_status", FILER)
        self.assertEqual((rs["used"], rs["max"]), (1, 5))

    def test_demo_rate_limit_is_smaller(self):
        w, bp, _ = F.deploy(rate_max=2, rate_window=600, demo=True)
        F.page(PAGE)
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(410), 0))
        F.model_answer("BURNED_PERCENT", "40%")
        w.call(bp, "file_claim", 1, TOKEN, SNAP, QUOTE, BLOCK, sender=FILER)
        w.call(bp, "file_claim", 1, TOKEN, SNAP, "never on the page at all", BLOCK, sender=FILER)
        with self.assertRaises(world.Reverted):
            w.call(bp, "file_claim", 1, TOKEN, SNAP, "never on the page again", BLOCK, sender=FILER)
        self.assertEqual(w.view(bp, "get_stats")["mode"], "DEMO")

    def test_counters(self):
        self.file()
        self.file(quote="burned 50% of the total supply")
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(100), 0))
        self.file(quote="has burned 40% of the total supply")
        s = self.stats()
        self.assertEqual((s["checks"], s["true"], s["false"], s["unverifiable"]), (3, 1, 1, 1))

    def test_counters_unchanged_by_refusals(self):
        self.file()
        before = self.stats()
        for k in ({"chain": 7}, {"block": 0}, {"quote": "short"}, {}):
            with self.assertRaises(world.Reverted):
                self.file(**k)
        self.assertEqual(self.stats(), before)

    def test_bad_constructor(self):
        w = world.new_world(now_iso=F.NOW_ISO)
        for args in (("LIVE", 5, 3600), ("CANONICAL", 0, 3600), ("CANONICAL", 5, 10), ("CANONICAL", 500, 3600)):
            with self.assertRaises(stub._UserError):
                w.deploy("BurnProof", *args)


# ---------------------------------------------------------------- consensus

class TestConsensus(Base):
    def test_validator_reading_differs_rolls_back(self):
        F.page("We burned 1,000,000 tokens.")
        F.set_token(1, TOKEN, 18, T(10 ** 9), (0, 0, T(10 ** 6), 0))
        stub.MODEL.answer = lambda p, n: {"type": "BURNED_AMOUNT" if n <= 2 else "SUPPLY_AT_MOST",
                                          "number": "1,000,000", "unit": ""}
        with self.assertRaises(world.Reverted) as cm:
            self.file(quote="We burned 1,000,000 tokens.")
        self.assertIn("UNDETERMINED", cm.exception.msg)
        self.assertEqual(self.stats()["checks"], 0)

    def test_forged_true_rejected(self):
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(100), 0))
        stub.FORGE["mutate"] = lambda r: dict(r, verdict="TRUE", code="BURNED_ENOUGH")
        with self.assertRaises(world.Reverted):
            self.file()
        self.assertEqual(self.stats()["checks"], 0)

    def test_forged_chain_numbers_rejected(self):
        def m(r):
            r["chain"]["burned"] = str(T(999))
            return r
        stub.FORGE["mutate"] = m
        with self.assertRaises(world.Reverted):
            self.file()

    def test_forged_claim_rejected(self):
        def m(r):
            r["claim"]["value"] = ["1", "1"]
            return r
        stub.FORGE["mutate"] = m
        with self.assertRaises(world.Reverted):
            self.file()

    def test_forged_quote_missing_rejected(self):
        stub.FORGE["payload"] = {"verdict": "UNVERIFIABLE", "code": "QUOTE_NOT_ON_PAGE", "why": "x", "stage": "page"}
        with self.assertRaises(world.Reverted):
            self.file()

    def test_leader_transport_unverifiable_accepted(self):
        stub.FORGE["payload"] = {"verdict": "UNVERIFIABLE", "code": "RPC_UNAVAILABLE", "why": "timeout", "stage": "chain"}
        r = self.file()
        self.assertEqual((r["verdict"], r["code"]), ("UNVERIFIABLE", "RPC_UNAVAILABLE"))

    def test_garbage_leader_rejected(self):
        stub.FORGE["payload"] = {"verdict": "MAYBE"}
        with self.assertRaises(world.Reverted):
            self.file()

    def test_validator_rpc_down_rejects_true(self):
        def hook():
            stub.WEB.down.add(F.ETH_A)
        stub.WEB.validator_hook = hook
        with self.assertRaises(world.Reverted):
            self.file()

    def test_validator_page_down_rejects_true(self):
        stub.WEB.validator_hook = lambda: stub.WEB.down.add(F.RAW)
        with self.assertRaises(world.Reverted):
            self.file()

    def test_validator_sees_same_unverifiable(self):
        r = self.file(quote="burned 50% of the total supply")
        self.assertTrue(stub.LAST_CONSENSUS["agreed"])
        self.assertEqual(r["code"], "QUOTE_NOT_ON_PAGE")

    def test_timeouts_end_unverifiable(self):
        stub.WEB.down.add("*")
        r = self.file()
        self.assertEqual((r["verdict"], r["code"]), ("UNVERIFIABLE", "PAGE_UNAVAILABLE"))

    def test_rpc_timeouts_end_unverifiable(self):
        stub.WEB.down.update([F.ETH_A, F.ETH_B])
        r = self.file()
        self.assertEqual((r["verdict"], r["code"]), ("UNVERIFIABLE", "RPC_UNAVAILABLE"))

    def test_every_accepted_filing_is_final(self):
        cases = [QUOTE, "burned 50% of the total supply", "has burned 40% of the total supply"]
        stub.WEB.down.add(F.ETH_B)
        for q in cases:
            r = self.file(quote=q)
            self.assertIn(r["verdict"], ("TRUE", "FALSE", "UNVERIFIABLE"))

    def test_model_unclear_leader_accepted(self):
        stub.MODEL.answer = {"type": "NONE", "number": "", "unit": ""}
        r = self.file()
        self.assertEqual(r["code"], "NOT_A_BURN_CLAIM")
        self.assertTrue(stub.LAST_CONSENSUS["agreed"])


# ---------------------------------------------------------------- views

class TestViews(Base):
    def test_get_check_missing(self):
        self.assertFalse(self.w.view(self.bp, "get_check", 7)["found"])
        self.assertFalse(self.w.view(self.bp, "get_check", 0)["found"])

    def test_list_checks_paging(self):
        for i in range(4):
            self.file(quote="quote number " + "x" * i, sender=[FILER, FILER2][i % 2])
        page = self.w.view(self.bp, "list_checks", 2, 2)
        self.assertEqual([c["check_id"] for c in page["checks"]], [2, 3])
        self.assertEqual(page["total"], 4)

    def test_list_checks_capped(self):
        self.file()
        self.assertEqual(len(self.w.view(self.bp, "list_checks", 1, 10 ** 6)["checks"]), 1)

    def test_list_checks_empty(self):
        self.assertEqual(self.w.view(self.bp, "list_checks", 1, 10)["checks"], [])

    def test_latest_verdict_none(self):
        lv = self.w.view(self.bp, "latest_verdict", 1, TOKEN, "")
        self.assertEqual((lv["verdict"], lv["decisive_verdict"], lv["latest"]), ("NONE", "NONE", None))

    def test_latest_is_by_snapshot_time_not_filing_order(self):
        F.page(PAGE, ts="20220101000000")
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(100), 0))
        self.file(snap=F.snap_url("20220101000000"))          # FALSE, newer snapshot
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(410), 0))
        stub.WEB.chains[F.ETH_A].set_block(BLOCK + 1, F.BLOCK_TS + 12)
        stub.WEB.chains[F.ETH_B].set_block(BLOCK + 1, F.BLOCK_TS + 12)
        self.file(block=BLOCK + 1)                               # TRUE, older snapshot, filed later
        lv = self.w.view(self.bp, "latest_verdict", 1, TOKEN, "")
        self.assertEqual(lv["decisive_verdict"], "FALSE")

    def test_latest_newer_true_wins(self):
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(100), 0))
        self.file()                                              # FALSE at TS
        F.page(PAGE, ts="20220101000000")
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(410), 0))
        self.file(snap=F.snap_url("20220101000000"))             # TRUE, newer
        self.assertEqual(self.w.view(self.bp, "latest_verdict", 1, TOKEN, "")["decisive_verdict"], "TRUE")

    def test_false_wins_tie(self):
        F.page(PAGE + " Also: we have burned 30% of all tokens.")
        self.file()                                              # TRUE
        F.model_answer("BURNED_PERCENT", "30%")
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(250), 0))
        stub.WEB.chains[F.ETH_A].set_block(BLOCK + 1, F.BLOCK_TS + 12)
        stub.WEB.chains[F.ETH_B].set_block(BLOCK + 1, F.BLOCK_TS + 12)
        self.file(quote="we have burned 30% of all tokens", block=BLOCK + 1)  # FALSE, same snapshot
        self.assertEqual(self.w.view(self.bp, "latest_verdict", 1, TOKEN, "")["decisive_verdict"], "FALSE")

    def test_unverifiable_is_not_decisive(self):
        self.file()                                              # TRUE
        F.page(PAGE, ts="20220101000000")
        self.file(snap=F.snap_url("20220101000000"), quote="burned 50% of the total supply")  # UNVERIFIABLE newer
        lv = self.w.view(self.bp, "latest_verdict", 1, TOKEN, "")
        self.assertEqual((lv["verdict"], lv["decisive_verdict"]), ("UNVERIFIABLE", "TRUE"))

    def test_host_filter(self):
        F.page(PAGE, site="other.io")
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(100), 0))
        self.file(snap=F.snap_url(site="other.io"))             # FALSE from other.io
        self.assertEqual(self.w.view(self.bp, "latest_verdict", 1, TOKEN, SITE)["decisive_verdict"], "NONE")
        self.assertEqual(self.w.view(self.bp, "latest_verdict", 1, TOKEN, "other.io")["decisive_verdict"], "FALSE")

    def test_counts(self):
        self.file()
        self.file(quote="burned 50% of the total supply")
        lv = self.w.view(self.bp, "latest_verdict", 1, TOKEN, "")
        self.assertEqual(lv["counts"], {"TRUE": 1, "FALSE": 0, "UNVERIFIABLE": 1})

    def test_tokens_are_separate(self):
        self.file()
        self.assertEqual(self.w.view(self.bp, "latest_verdict", 1, TOKEN9, "")["verdict"], "NONE")
        self.assertEqual(self.w.view(self.bp, "latest_verdict", 56, TOKEN, "")["verdict"], "NONE")

    def test_get_rules(self):
        r = self.w.view(self.bp, "get_rules")
        self.assertEqual(r["dead_addresses"], list(BP.DEAD))
        self.assertEqual(r["tolerance"], "0.5%")
        self.assertEqual(sorted(r["chains"]), ["1", "56"])

    def test_stats_fresh(self):
        s = self.stats()
        self.assertEqual((s["checks"], s["mode"], s["rate_max"]), (0, "CANONICAL", 5))


# ---------------------------------------------------------------- the consumer gate

class TestGate(Base):
    def req(self, site=SITE, token=TOKEN, chain=1):
        return self.w.call(self.gate, "request_listing", chain, token, site, sender=PROJECT)

    def test_allow_true(self):
        self.file()
        r = self.req()
        self.assertTrue(r["listed"])
        self.assertTrue(self.w.view(self.gate, "is_listed", 1, TOKEN)["listed"])

    def test_allow_no_claim(self):
        r = self.req()
        self.assertTrue(r["listed"])
        self.assertEqual(r["verdict"], "NONE")

    def test_refuse_false(self):
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(100), 0))
        self.file()
        r = self.req()
        self.assertFalse(r["listed"])
        self.assertEqual((r["verdict"], r["check_id"]), ("FALSE", 1))
        self.assertFalse(self.w.view(self.gate, "is_listed", 1, TOKEN)["listed"])

    def test_unverifiable_does_not_refuse(self):
        self.file(quote="burned 50% of the total supply")
        self.assertTrue(self.req()["listed"])

    def test_refusal_is_logged(self):
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(100), 0))
        self.file()
        self.req()
        g = self.w.view(self.gate, "get_request", 1)
        self.assertEqual((g["found"], g["listed"], g["site"]), (True, False, SITE))
        self.assertEqual(self.w.view(self.gate, "get_stats")["refused"], 1)

    def test_false_on_another_site_does_not_refuse(self):
        F.page(PAGE, site="griefer.io")
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(100), 0))
        self.file(snap=F.snap_url(site="griefer.io"))
        self.assertTrue(self.req()["listed"])

    def test_later_filing_of_older_snapshot_cannot_mask(self):
        F.page(PAGE, ts="20220101000000")
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(100), 0))
        self.file(snap=F.snap_url("20220101000000"))
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(410), 0))
        stub.WEB.chains[F.ETH_A].set_block(BLOCK + 1, F.BLOCK_TS + 12)
        stub.WEB.chains[F.ETH_B].set_block(BLOCK + 1, F.BLOCK_TS + 12)
        self.file(block=BLOCK + 1)
        self.assertFalse(self.req()["listed"])

    def test_unverifiable_cannot_mask_false(self):
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(100), 0))
        self.file()
        F.page(PAGE, ts="20220101000000")
        self.file(snap=F.snap_url("20220101000000"), quote="burned 50% of the total supply")
        self.assertFalse(self.req()["listed"])

    def test_delisted_after_false(self):
        self.file()
        self.assertTrue(self.req()["listed"])
        F.page(PAGE, ts="20220101000000")
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(100), 0))
        stub.WEB.chains[F.ETH_A].set_block(BLOCK + 1, F.BLOCK_TS + 12)
        stub.WEB.chains[F.ETH_B].set_block(BLOCK + 1, F.BLOCK_TS + 12)
        self.file(snap=F.snap_url("20220101000000"), block=BLOCK + 1)
        self.assertFalse(self.req()["listed"])
        self.assertFalse(self.w.view(self.gate, "is_listed", 1, TOKEN)["listed"])

    def test_bad_site(self):
        for s in ("", "nodot", "a..b.io", "evil site.io", "https://x.io"):
            with self.assertRaises(world.Reverted):
                self.req(site=s)

    def test_bad_token(self):
        with self.assertRaises(world.Reverted):
            self.req(token="0x12")

    def test_site_case_insensitive(self):
        F.set_token(1, TOKEN, 18, T(1000), (0, 0, T(100), 0))
        self.file()
        self.assertFalse(self.req(site=SITE.upper())["listed"])

    def test_unreadable_burnproof(self):
        w = self.w
        g2 = w.deploy("BurnGate", F.addr(4242))
        with self.assertRaises(world.Reverted) as cm:
            w.call(g2, "request_listing", 1, TOKEN, SITE, sender=PROJECT)
        self.assertIn("BURNPROOF_UNREADABLE", cm.exception.msg)

    def test_gate_list_requests(self):
        self.req()
        self.req(token=TOKEN9)
        self.assertEqual(len(self.w.view(self.gate, "list_requests", 1, 10)["requests"]), 2)

    def test_gate_missing_request(self):
        self.assertFalse(self.w.view(self.gate, "get_request", 3)["found"])

    def test_gate_bad_constructor(self):
        with self.assertRaises(stub._UserError):
            self.w.deploy("BurnGate", "nope")


# ---------------------------------------------------------------- pure helpers

class TestHelpers(unittest.TestCase):
    def test_page_text(self):
        self.assertEqual(BP.page_text("<p>a&amp;b</p>\n<p>c</p>"), "a&b c")

    def test_memento_format(self):
        self.assertEqual(BP.memento_of(BP.parse_ts("20210902070016")), "02 Sep 2021 07:00:16 GMT")

    def test_epoch(self):
        self.assertEqual(BP.epoch_of(1970, 1, 1, 0, 0, 0), 0)
        self.assertEqual(BP.epoch_of(2021, 9, 2, 7, 0, 16), 1630566016)

    def test_iso_epoch(self):
        self.assertEqual(BP.iso_epoch("2021-09-02T07:00:16Z"), 1630566016)
        self.assertEqual(BP.iso_epoch("bad"), 0)

    def test_host_of(self):
        self.assertEqual(BP.host_of("https://WWW.Akita.Network/x"), "www.akita.network")
        self.assertEqual(BP.host_of("https://a.io:443/"), "a.io")
        self.assertEqual(BP.host_of("https://a.io:8080/"), "")

    def test_fmt_units(self):
        self.assertEqual(BP.fmt_units(1234567 * 10 ** 14, 18), "123.4567")
        self.assertEqual(BP.fmt_units(10 ** 22, 18), "10,000.0000")

    def test_fmt_pct(self):
        self.assertEqual(BP.fmt_pct(1, 3), "33.3333%")

    def test_frac(self):
        self.assertEqual(BP._frac(782, 100), [391, 50])

    def test_decide_is_pure_integer(self):
        d = BP.decide("BURNED_PERCENT", ["40", "1"], {"decimals": 18, "supply": str(T(1000)), "burned": str(T(398))})
        self.assertEqual(d["verdict"], "TRUE")


# ---------------------------------------------------------------- static checks

class TestStatic(unittest.TestCase):
    FILES = sorted((ROOT / "contracts").glob("*.py"))

    def test_header(self):
        for f in self.FILES:
            lines = f.read_text().split("\n")
            self.assertEqual(lines[0], "# v0.3.0", f.name)
            self.assertEqual(lines[1], '# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }', f.name)

    def test_no_undefined_names(self):
        for f in self.FILES:
            self.assertEqual(stub.undefined_names(f), [], f.name)

    def test_views_do_not_write_or_reach_out(self):
        for f in self.FILES:
            tree = ast.parse(f.read_text())
            for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
                for fn in [n for n in cls.body if isinstance(n, ast.FunctionDef)]:
                    if not any(ast.unparse(d) == "gl.public.view" for d in fn.decorator_list):
                        continue
                    for n in ast.walk(fn):
                        if isinstance(n, (ast.Assign, ast.AugAssign)):
                            for t in (n.targets if isinstance(n, ast.Assign) else [n.target]):
                                self.assertFalse(ast.unparse(t).startswith("self."), f.name + "." + fn.name)
                        if isinstance(n, ast.Call) and ast.unparse(n.func).endswith(("run_nondet", "exec_prompt", "web.request")):
                            self.fail(f.name + "." + fn.name)

    def test_no_value_handling(self):
        for f in self.FILES:
            t = f.read_text()
            self.assertNotIn("payable", t, f.name)
            self.assertNotIn("emit_transfer", t, f.name)

    def test_no_owner_or_setter(self):
        for f in self.FILES:
            t = f.read_text()
            self.assertNotIn("self.owner", t, f.name)
            self.assertNotIn("self.admin", t, f.name)
            self.assertNotIn("def set_", t, f.name)

    def test_storage_annotations(self):
        t = (ROOT / "contracts" / "BurnProof.py").read_text()
        self.assertIn("gl.storage.TreeMap[u64, Check]", t)
        self.assertIn("@gl.storage.allow", t)

    def test_dead_list_frozen(self):
        self.assertEqual(BP.DEAD, ("0x0000000000000000000000000000000000000000",
                                   "0x0000000000000000000000000000000000000001",
                                   "0x000000000000000000000000000000000000dead",
                                   "0xdead000000000000000042069420694206942069"))

    def test_ascii_source(self):
        for f in self.FILES:
            f.read_text().encode("ascii")


if __name__ == "__main__":
    unittest.main()
