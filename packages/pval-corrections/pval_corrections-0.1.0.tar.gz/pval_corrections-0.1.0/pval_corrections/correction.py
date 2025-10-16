
p_values = []

def bonferroni_correction(p_values):
    padj={
        'p originals': p_values,
        'padj': []
    }
    m=len(p_values)
    for i in range(m):
        padj['padj'].append(p_values[i] * m)
    return padj

def bh_formula(p, m, i):
    return p * m / i

def benjamini_hochberg_correction(p_values):
    padj={
        'p originals': p_values,
        'padj': []
    }
    m=len(p_values)
    for i in range(m):
        padj['padj'].append(bh_formula(p_values[i], m, i + 1))
    return padj

correction_methods = ['bonferroni', 'benjamini_hochberg']
def correction(p_values, correction_method):
    if correction_method == 'benjamini_hochberg':
        return benjamini_hochberg_correction(p_values)
    elif correction_method == 'bonferroni':
        return bonferroni_correction(p_values)

# p_values = [0.01, 0.02, 0.03, 0.04, 0.05]
# correction_method = 'bf'
# padj = correction(p_values, correction_method)
# print(padj)



        
    

