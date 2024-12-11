from django.shortcuts import render
from concurrent.futures import ThreadPoolExecutor

def pad_message(message, size):
    while len(message) % size != 0:
        message += " "
    return message

def text_to_numbers(text):
    return [ord(char) for char in text]

def numbers_to_text(numbers):
    return "".join(chr(num) for num in numbers)

def gaussian_inversion(matrix, parallel=False):
    size = len(matrix)
    augmented = [row + [1 if i == j else 0 for j in range(size)] for i, row in enumerate(matrix)]

    def forward_elimination():
        for i in range(size):
            pivot = augmented[i][i]
            if pivot == 0:
                raise ValueError("Matrix is not invertible.")
            for j in range(2 * size):
                augmented[i][j] /= pivot
            for k in range(i + 1, size):
                factor = augmented[k][i]
                for j in range(2 * size):
                    augmented[k][j] -= factor * augmented[i][j]

    def back_substitution():
        for i in range(size - 1, -1, -1):
            for k in range(i - 1, -1, -1):
                factor = augmented[k][i]
                for j in range(2 * size):
                    augmented[k][j] -= factor * augmented[i][j]

    if parallel:
        with ThreadPoolExecutor() as executor:
            executor.submit(forward_elimination).result()
            executor.submit(back_substitution).result()
    else:
        forward_elimination()
        back_substitution()

    inverse = [row[size:] for row in augmented]
    return inverse

def lu_decomposition(matrix):
    size = len(matrix)
    L = [[0.0] * size for _ in range(size)]
    U = [[0.0] * size for _ in range(size)]
    for i in range(size):
        for j in range(i, size):
            U[i][j] = matrix[i][j] - sum(L[i][k] * U[k][j] for k in range(i))
        L[i][i] = 1.0
        for j in range(i + 1, size):
            L[j][i] = (matrix[j][i] - sum(L[j][k] * U[k][i] for k in range(i))) / U[i][i]
    return L, U

def inverse_using_lu(L, U, size, parallel=False):
    def forward_substitution(L, b):
        y = [0] * size
        for i in range(size):
            y[i] = b[i] - sum(L[i][j] * y[j] for j in range(i))
        return y

    def backward_substitution(U, y):
        x = [0] * size
        for i in range(size - 1, -1, -1):
            x[i] = (y[i] - sum(U[i][j] * x[j] for j in range(i + 1, size))) / U[i][i]
        return x

    inverse = []
    if parallel:
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(lambda b: backward_substitution(U, forward_substitution(L, b)), [1 if i == j else 0 for j in range(size)])
                for i in range(size)
            ]
            inverse = [future.result() for future in futures]
    else:
        for i in range(size):
            b = [1 if i == j else 0 for j in range(size)]
            y = forward_substitution(L, b)
            inverse.append(backward_substitution(U, y))
    return list(map(list, zip(*inverse)))


def decrypt_message(encrypted_msg, matrix_inverse, size):
    msg_matrix = [encrypted_msg[i:i + size] for i in range(0, len(encrypted_msg), size)]
    decrypted_matrix = matrix_multiply(msg_matrix, matrix_inverse)
    flattened = [round(value) for row in decrypted_matrix for value in row]
    return numbers_to_text(flattened).strip()
def matrix_multiply(A, B):
    rows_A, cols_A = len(A), len(A[0])
    rows_B, cols_B = len(B), len(B[0])
    if cols_A != rows_B:
        raise ValueError("Matrix dimensions do not allow multiplication.")

    result = [[0] * cols_B for _ in range(rows_A)]

    def compute_entry(i, j):
        return sum(A[i][k] * B[k][j] for k in range(cols_A))

    with ThreadPoolExecutor() as executor:
        futures = {(i, j): executor.submit(compute_entry, i, j) for i in range(rows_A) for j in range(cols_B)}
        for (i, j), future in futures.items():
            result[i][j] = future.result()
    return result

def encrypt_message(message, matrix):
    size = len(matrix)
    padded_msg = pad_message(message, size)
    msg_numbers = text_to_numbers(padded_msg)
    msg_matrix = [msg_numbers[i:i+size] for i in range(0, len(msg_numbers), size)]
    encrypted_matrix = matrix_multiply(msg_matrix, matrix)
    # Return the encrypted message as a space-separated string
    encrypted_values = [int(value) for row in encrypted_matrix for value in row]
    return ' '.join(map(str, encrypted_values))

def matrix_view(request):
    size = None
    matrix = []
    operation = None
    error_message = None
    encrypted_message = None
    decrypted_message = None
    matrix_inverse = None
    decompose_method = None
    inversion_mode = None
    message = request.POST.get("message", "").split()
    if request.method == 'POST':
        try:
   
            operation = request.POST.get("operation")
            decompose_method = request.POST.get("decompose_method", "LU")
            inversion_mode = request.POST.get("inversion_mode", "Sequential")
            size = int(request.POST.get("size", 0))

  
            if size <= 0 and message:
                raise ValueError("Matrix size must be greater than zero.")


            for i in range(size):
                row = [int(request.POST.get(f"matrix_{i}_{j}", 0)) for j in range(size)]
                matrix.append(row)


            if operation == "encrypt":
                message = request.POST.get("message", "")
                if not message and size:
                    raise ValueError("Message cannot be empty for encryption.")
                if operation == "encrypt":
                    encrypted_message = encrypt_message(message, matrix)


            elif operation == "decrypt":
                if decompose_method == "Gaussian":
                    matrix_inverse = gaussian_inversion(matrix, parallel=(inversion_mode == "Parallel"))
                elif decompose_method == "LU":
                    L, U = lu_decomposition(matrix)
                    matrix_inverse = inverse_using_lu(L, U, size, parallel=(inversion_mode == "Parallel"))

                encrypted_values = list(map(int, message))
                decrypted_message = decrypt_message(encrypted_values, matrix_inverse, size)
            

            else:
                raise ValueError("Invalid operation selected.")
        
        except Exception as e:
            error_message = f"Error: {e}"


    context = {
        "size": size,
        "matrix": matrix,
        "operation": operation,
        "decompose_method": decompose_method,
        "inversion_mode": inversion_mode,
        "error_message": error_message,
        "encrypted_message": encrypted_message,
        "decrypted_message": decrypted_message,
        "matrix_inverse": matrix_inverse,
    }
    return render(request, 'encrypter/form.html', context)
