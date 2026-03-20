package dev.cdelmonte.collecting.rightsholder;

import java.util.Objects;
import java.util.UUID;

/**
 * Legal entity holding exploitation rights for musical works.
 * A rights holder has signed a mandate with the collecting society
 * and receives royalty payments from distribution runs.
 */
public class RightsHolder {

    private final UUID id;
    private String name;
    private String ipiNumber;       // International Publisher/Producer Identifier
    private String bankAccount;     // IBAN for royalty payouts

    public RightsHolder(UUID id, String name, String ipiNumber, String bankAccount) {
        this.id = Objects.requireNonNull(id, "id must not be null");
        this.name = Objects.requireNonNull(name, "name must not be null");
        this.ipiNumber = ipiNumber;
        this.bankAccount = bankAccount;
    }

    public UUID getId() { return id; }
    public String getName() { return name; }
    public String getIpiNumber() { return ipiNumber; }
    public String getBankAccount() { return bankAccount; }

    public void setName(String name) { this.name = name; }
    public void setIpiNumber(String ipiNumber) { this.ipiNumber = ipiNumber; }
    public void setBankAccount(String bankAccount) { this.bankAccount = bankAccount; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof RightsHolder other)) return false;
        return Objects.equals(id, other.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }
}
