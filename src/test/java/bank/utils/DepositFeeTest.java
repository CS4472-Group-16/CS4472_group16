package bank.utils;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvFileSource;

/** Assignment 1, Deposit: weak robust equivalence class analysis. */
class DepositFeeTest {
    @ParameterizedTest(name = "{0}")
    @CsvFileSource(resources = "/assignment1/deposit.csv", numLinesToSkip = 1)
    void deposit(String id, double amount, double balance, boolean student, String expected) {
        FeesCalculator calculator = new FeesCalculator();
        if ("REJECT".equals(expected)) {
            // Explicit invalid-input assumption; see docs/assignment1.md.
            assertThrows(IllegalArgumentException.class,
                    () -> calculator.calculateDepositInterest(amount, balance, student), id);
        } else {
            assertEquals(Double.parseDouble(expected),
                    calculator.calculateDepositInterest(amount, balance, student), 1.0e-9, id);
        }
    }
}
