package bank.utils;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvFileSource;

/** Assignment 1, Transfer: each row is one complete decision-table rule. */
class TransferFeeTest {
    @ParameterizedTest(name = "{0}")
    @CsvFileSource(resources = "/assignment1/transfer.csv", numLinesToSkip = 1)
    void transfer(String id, double amount, double from, double to, boolean student,
            double rate, double expected) {
        assertEquals(expected,
                new FeesCalculator().calculateTransferFee(amount, from, to, student), 1.0e-9, id);
        assertEquals(expected, amount * rate, 1.0e-9, id + " decision-table oracle");
    }
}
