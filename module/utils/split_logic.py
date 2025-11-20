def count_the_bill(receipt, assignment):
    total = {}

    subtotal = receipt.subtotal or 0
    tax = receipt.tax or 0
    service = receipt.service_charge or 0
    others = receipt.others or 0

    for idx, item in enumerate(receipt.items):
        payers = assignment.get(idx, [])
        if not payers:
            continue

        proportion = item.total_price / subtotal if subtotal > 0 else 0

        tax_share     = tax     * proportion
        service_share = service * proportion
        others_share  = others  * proportion

        final_price = item.total_price + tax_share + service_share + others_share

        share_per_person = final_price / len(payers)

        for p in payers:
            total[p] = total.get(p, 0) + share_per_person

    return total