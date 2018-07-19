#include "test_prj1.h"
#include "ui_test_prj1.h"

Test_Prj1::Test_Prj1(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::Test_Prj1)
{
    ui->setupUi(this);
}

Test_Prj1::~Test_Prj1()
{
    delete ui;
}
