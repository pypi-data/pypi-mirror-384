from mrn.paraconsistent.block import ParaconsistentBlock

def main():
    b1 = ParaconsistentBlock()
    b2 = ParaconsistentBlock()

    b1.input(mu=0.08, lam=0.97)
    b1.config.FL = 0.75

    b2.input.mu = 0.5 * b1.complete.gc + 0.1

    print("=== B1.complete ===")
    b1.print_complete()

    print("=== B2.complete ===")
    b2.print_complete()

if __name__ == "__main__":
    main()
