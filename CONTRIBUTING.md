# Contributing

Corrections are welcome, especially when a vendor changes its pricing or adds AI Mode to a plan.

## Changing a tool

1. Edit the tool's entry in `tools.yaml`. Keep prices in the vendor's own currency.
2. If AI Mode moved in or out of the base plan, update `ai_mode` to one of `included`, `addon`, `product`, `unclear` or `absent`.
3. Regenerate the table:

   ```bash
   pip install -r requirements.txt
   python render_table.py --write
   python render_table.py --check
   ```

4. Open a pull request and link the public page that shows the change, such as a pricing page or changelog entry.

## What gets accepted

- Facts a reader can check on the vendor's own site.
- One specific limitation per tool, not a generic complaint.

## What gets declined

- Ratings or scores, including ones a vendor publishes about competitors.
- Affiliate links or tracking parameters in any URL.
- Engine claims with no public source.
