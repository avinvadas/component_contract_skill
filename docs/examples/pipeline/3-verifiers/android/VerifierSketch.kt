// ILLUSTRATIVE — not compiled or run in this repo.
//
// Shape of an Android verifier. Same canonical document, different tool. Runs under
// Robolectric on the JVM, so it needs no emulator — the `mounted` tier, not `driven`.

import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test

class ContractVerifier {
    @get:Rule val compose = createComposeRule()

    private val doc = CanonicalDocument.load("Button.android.canonical.json")
    private val capability = Capability.load("capability.json")

    @Test fun verifyContract() {
        for (req in doc.requirements) {
            if (req.binds == false) { record(NotApplicable(req, req.reason)); continue }

            val missing = req.needs.firstOrNull { it in capability.cannotObserve }
            // JUnit's Assume is the native third state — a skipped test carrying its reason.
            assumeTrue("${req.id} — unverified: ${capability.cannotObserve[missing]}", missing == null)

            val witness = Witness.matching(req.scenario) ?: Witness.construct(req.scenario)
            assumeTrue("${req.id} — unverified: no witness satisfies ${req.scenario}", witness != null)

            compose.setContent { witness!!.render() }
            val node = compose.onNodeWithTag("root")

            when (req.observe) {
                "role"   -> node.assertRoleEquals(req.expect.equals())
                "name"   -> node.assertContentDescriptionIsNotEmpty()
                "state"  -> node.assertStateContains(req.expect.contains())
                "focus"  -> node.assertFocusable(req.expect.equals<Boolean>())
                "layout" -> node.assertMinimumTouchTargetSize(req.expect.min().dp)
                "order"  -> node.assertZoneOrder(req.expect.order())
                else     -> assumeTrue("${req.id} — observe ${req.observe} not implemented", false)
            }
        }
    }
}
