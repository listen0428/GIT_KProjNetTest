#ifndef TEST_PRJ1_H
#define TEST_PRJ1_H

#include <QWidget>

namespace Ui {
class Test_Prj1;
}

class Test_Prj1 : public QWidget
{
    Q_OBJECT

public:
    explicit Test_Prj1(QWidget *parent = 0);
    ~Test_Prj1();

private:
    Ui::Test_Prj1 *ui;
};

#endif // TEST_PRJ1_H
