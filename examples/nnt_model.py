import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

import optscale_arcee as arcee


def main():
    # init arcee
    with arcee.init(
        "2f4fda2d-755a-45a1-95d9-d9406606af1e",
        task_key="test_task",
        endpoint_url="https://10.10.10.10:443/arcee/v2",
        ssl=False,
    ):
        arcee.tag("project", "nnt_model demo")
        arcee.tag("model_type", "trivial")

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Hyperparameters
        input_size = 784
        hidden_size = 128
        num_classes = 10
        num_epochs = 5
        batch_size = 64
        learning_rate = 0.001

        # Dataset and DataLoader
        transform = transforms.Compose(
            [
                transforms.ToTensor(),
                transforms.Normalize((0.1307,), (0.3081,)),
                # MNIST-spec normalization
            ]
        )

        print("Downloading datasets..")
        arcee.milestone("Download train data")
        train_dataset = datasets.MNIST(
            root="data", train=True, transform=transform, download=True
        )
        arcee.milestone("Download test data")
        test_dataset = datasets.MNIST(
            root="data", train=False, transform=transform, download=True
        )

        train_loader = DataLoader(
            dataset=train_dataset, batch_size=batch_size, shuffle=True
        )
        test_loader = DataLoader(
            dataset=test_dataset, batch_size=batch_size, shuffle=False
        )

        # Neural Net
        class NeuralNet(nn.Module):
            def __init__(self):
                super(NeuralNet, self).__init__()
                self.fc1 = nn.Linear(input_size, hidden_size)
                self.relu = nn.ReLU()
                self.fc2 = nn.Linear(hidden_size, num_classes)

            def forward(self, x):
                x = x.view(-1, 28 * 28)  # flatten
                x = self.fc1(x)
                x = self.relu(x)
                x = self.fc2(x)
                return x

        model = NeuralNet().to(device)

        # Loss and Optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)

        # Training
        print("Training..")
        arcee.milestone("train")
        for epoch in range(num_epochs):
            model.train()
            total_loss = 0
            correct = 0
            total = 0

            for images, labels in train_loader:
                images, labels = images.to(device), labels.to(device)

                outputs = model(images)
                loss = criterion(outputs, labels)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                total_loss += loss.item()
                _, predicted = torch.max(outputs, 1)
                correct += (predicted == labels).sum().item()
                total += labels.size(0)

            train_acc = 100 * correct / total
            avg_loss = total_loss / len(train_loader)

            arcee.send({"accuracy": train_acc,
                        "loss": avg_loss, "epoch": epoch + 1})
            arcee.send({"loss": f"{avg_loss:.2f}%"})
            arcee.send({"epoch": f"[{epoch + 1}/{num_epochs}]"})
            print(
                f"Epoch [{epoch + 1}/{num_epochs}], "
                f"Loss: {avg_loss:.4f}, Accuracy: {train_acc:.2f}%"
            )

        # Testing
        print("Testing..")
        arcee.milestone("test")
        model.eval()
        with torch.no_grad():
            correct = 0
            total = 0
            for images, labels in test_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
            arcee.send({"test_accuracy": 100 * correct / total})
            print(f"Test Accuracy: {100 * correct / total:.2f}%")


if __name__ == "__main__":
    main()
