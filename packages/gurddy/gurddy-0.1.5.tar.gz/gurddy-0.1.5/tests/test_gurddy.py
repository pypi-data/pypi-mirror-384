# tests/test_gurddy.py (Example test for Sudoku using CSP)
import gurddy

def test_sudoku():
    model = gurddy.Model("Sudoku", "CSP")
    
    # Define variables for Sudoku
    vars = {}
    for r in range(1, 10):
        for c in range(1, 10):
            name = f'R{r}C{c}'
            vars[name] = model.addVar(name, domain=list(range(1, 10)))

    # Add AllDifferent constraints for rows
    for r in range(1, 10):
        row_vars = [vars[f'R{r}C{c}'] for c in range(1, 10)]
        model.addConstraint(gurddy.AllDifferentConstraint(row_vars))

    # Columns
    for c in range(1, 10):
        col_vars = [vars[f'R{r}C{c}'] for r in range(1, 10)]
        model.addConstraint(gurddy.AllDifferentConstraint(col_vars))

    # Boxes
    for br in range(3):
        for bc in range(3):
            box_vars = []
            for r in range(3):
                for c in range(3):
                    box_vars.append(vars[f'R{br*3 + r + 1}C{bc*3 + c + 1}'])
            model.addConstraint(gurddy.AllDifferentConstraint(box_vars))

    # Set initial values (from the puzzle)
    puzzle = [
        [0, 0, 0, 0, 0, 0, 0, 0, 3],
        [0, 0, 0, 0, 6, 3, 0, 4, 0],
        [0, 0, 4, 0, 0, 2, 6, 9, 7],
        [0, 9, 0, 7, 0, 0, 3, 1, 0],
        [3, 0, 0, 0, 0, 0, 0, 6, 4],
        [8, 0, 0, 0, 5, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 8, 2, 0, 0],
        [0, 7, 8, 0, 0, 0, 0, 0, 0],
        [4, 0, 2, 0, 0, 0, 0, 0, 0]
    ]
    for r in range(9):
        for c in range(9):
            if puzzle[r][c] != 0:
                var = vars[f'R{r+1}C{c+1}']
                model.addConstraint(var == puzzle[r][c])

    solution = model.solve()
    assert solution is not None
    # Print solution if needed
    # for r in range(1, 10):
    #     row = [solution[f'R{r}C{c}'] for c in range(1, 10)]
    #     print(' '.join(map(str, row)))

# Run test
if __name__ == "__main__":
    test_sudoku()
    print("Sudoku test passed.")