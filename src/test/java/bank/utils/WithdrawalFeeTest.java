package bank.utils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvFileSource;

/** Assignment 1, Withdrawal: robust worst-case boundary value analysis. */
class WithdrawalFeeTest {
    @ParameterizedTest(name = "{0}")
    @CsvFileSource(resources = "/assignment1/withdrawal.csv", numLinesToSkip = 1)
    void withdrawal(String id, double amount, double balance, boolean student, int day,
            String expected) {
        FeesCalculator calculator = new FeesCalculator();
        if ("REJECT".equals(expected)) {
            // Explicit invalid-input assumption; see docs/assignment1.md.
            assertThrows(IllegalArgumentException.class,
                    () -> calculator.calculateWithdrawalFee(amount, balance, student, day), id);
        } else {
            assertEquals(Double.parseDouble(expected),
                    calculator.calculateWithdrawalFee(amount, balance, student, day), 1.0e-9, id);
        }
    }
}
