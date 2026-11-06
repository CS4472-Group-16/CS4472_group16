package atm.session;

import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import atm.ATM;
import atm.dispatcher.JavaDispatcher;
import atm.dispatcher.MessageDispatcher;
import atm.exceptions.InvalidAmountException;
import atm.exceptions.InvalidPinFormatException;
import atm.session.transactions.ATMWithdrawal;
import atm.ui.panels.MainPanel;
import atm.utils.CredentialsCheck;
import atm.utils.FormatChecker;
import bank.BankFacade;
import bank.db.DBHandler;
import bank.transactions.BankWithdrawal;
import bank.transactions.utils.AccountType;
import bank.utils.FeesCalculator;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvFileSource;

/** Assignment 1, ATM Session: boundary analysis with one invalid input at a time. */
class SessionTest {
    private static final String CARD = "4000000000000000";
    private static final double BALANCE = 5000.0;
    private static final int DAILY_LIMIT = 1000;

    @ParameterizedTest(name = "{0}")
    @CsvFileSource(resources = "/assignment1/pin.csv", numLinesToSkip = 1)
    void pin(String id, String pin, boolean valid) {
        char[] input = pin == null ? new char[0] : pin.toCharArray();
        // Format validation is exposed by ATM.checkPin, ahead of Session.addPin.
        MessageDispatcher dispatcher = mock(MessageDispatcher.class);
        when(dispatcher.checkCredentials(anyString(), any(char[].class))).thenReturn(true);
        ATM atm = new ATM(new FormatChecker(), new CredentialsCheck(dispatcher), dispatcher);
        atm.setMainPanel(mock(MainPanel.class));
        atm.createSession();
        assertDoesNotThrow(() -> atm.checkCardNumber(CARD));
        if (valid) {
            assertDoesNotThrow(() -> atm.checkPin(input), id);
        } else {
            assertThrows(InvalidPinFormatException.class, () -> atm.checkPin(input), id);
        }
    }

    @ParameterizedTest(name = "{0}")
    @CsvFileSource(resources = "/assignment1/session.csv", numLinesToSkip = 1)
    void withdrawalAmount(String id, String pin, int amount, boolean valid) throws Exception {
        // Fresh account fixture per case. No real database is created or modified.
        DBHandler account = mock(DBHandler.class);
        when(account.getCardOwner(CARD)).thenReturn("assignment1");
        when(account.getPIN("assignment1")).thenReturn(pin.toCharArray());
        when(account.getBalance("assignment1", AccountType.Chequing)).thenReturn(BALANCE);
        when(account.isStudent("assignment1")).thenReturn(false);
        // Isolate the Session target from the separately tested fee calculation.
        BankWithdrawal bankWithdrawal = new BankWithdrawal(mock(FeesCalculator.class), account);
        BankFacade bank = new BankFacade(account, bankWithdrawal, null, null);
        Session session = new Session(mock(MainPanel.class), new JavaDispatcher(bank));
        session.insertCard();
        session.addCard(CARD);
        // Direct Session API prevents the known PIN-format fault masking amount results.
        session.addPin(pin.toCharArray());
        session.setTransaction(new ATMWithdrawal()); // Console choice 1's transaction type.
        session.setFromAccount(AccountType.Chequing);
        if (valid) {
            assertTrue(amount <= DAILY_LIMIT, "fixture oracle must respect daily limit");
            assertDoesNotThrow(() -> session.setAmount(amount), id);
            assertTrue(session.result.isSuccessful(), id);
            assertEquals(BALANCE - amount, session.result.getAccountBalances()[0], 1.0e-9, id);
        } else {
            assertThrows(InvalidAmountException.class, () -> session.setAmount(amount), id);
        }
    }
}
