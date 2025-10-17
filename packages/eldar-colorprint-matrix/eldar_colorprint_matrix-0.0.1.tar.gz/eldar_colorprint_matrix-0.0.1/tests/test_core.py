from colorprint import print_color

def test_print_color(capsys):
    # print_color funksiyasına text və color argumentləri veririk
    print_color("Salam Eldar!", "red")
    print_color("Bu qirmizi rəngdə olacaq", "red")
    print_color("Bu mavi rəngdə olacaq", "blue")
    
    # çıxışı oxuyuruq
    captured = capsys.readouterr()
    
    # testlər
    assert "Salam Eldar!" in captured.out
    assert "Bu qirmizi rəngdə olacaq" in captured.out
    assert "Bu mavi rəngdə olacaq" in captured.out
